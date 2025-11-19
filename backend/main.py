"""
FastAPI Main Application - AbsenteismoController v2.0
"""
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query, Form, Request, status
from typing import List
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, nullslast, text
from typing import Optional, List
import os
import shutil
import json
from datetime import datetime
import uuid
from collections import OrderedDict
import pandas as pd
import time
from collections import defaultdict

from .database import get_db, init_db, run_migrations
from .models import Client, Upload, Atestado, User, Config, ClientColumnMapping, Produtividade, ClientLogo, SavedFilter
from .excel_processor import ExcelProcessor
from .analytics import Analytics
from .insights import InsightsEngine
from .logger import app_logger, error_logger, security_logger, audit_logger, log_audit, log_security, log_error, log_operation
from .upload_handler import save_upload_with_timeout, validate_file_upload
from .validators import validate_business_rules
# PDF removido
# ReportGenerator ainda usado para Excel e PPTX
try:
    from .report_generator import ReportGenerator
except ImportError:
    ReportGenerator = None
from .alerts import AlertasSystem
from .auth import (
    authenticate_user, create_access_token, get_current_active_user,
    get_current_admin_user, get_config_value, set_config_value,
    get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta
import requests
import re
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Request

# Initialize FastAPI app
app = FastAPI(
    title="AbsenteismoController",
    version="2.0.0",
    description="Sistema de Gestão de Absenteísmo"
)

# Exception handler global para garantir que todos os erros retornem JSON
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para capturar todos os erros não tratados"""
    import traceback
    
    # Se já é HTTPException, retorna como está
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # Log do erro
    error_traceback = traceback.format_exc()
    error_logger.error(
        f"Erro não tratado: {str(exc)}",
        exc_info=True,
        extra={
            'path': request.url.path,
            'method': request.method,
            'traceback': error_traceback
        }
    )
    
    # Retorna erro como JSON
    error_type = type(exc).__name__
    error_str = str(exc)
    
    # Em produção, mostra tipo de erro e mensagem resumida
    if os.getenv("ENVIRONMENT", "development") != "development":
        # Mensagens específicas por tipo de erro
        if "Permission" in error_type or "permission" in error_str.lower():
            error_message = "Erro de permissão. Verifique as permissões da pasta uploads/ no servidor."
        elif "FileNotFound" in error_type or "no such file" in error_str.lower():
            error_message = "Arquivo ou diretório não encontrado. Verifique se a pasta uploads/ existe."
        elif "Database" in error_type or "database" in error_str.lower() or "sql" in error_str.lower():
            error_message = "Erro no banco de dados. Verifique a conexão e as tabelas."
        elif "JSON" in error_type or "json" in error_str.lower():
            error_message = "Erro ao processar dados JSON. Verifique o formato da planilha."
        elif "pandas" in error_str.lower() or "excel" in error_str.lower():
            error_message = "Erro ao processar planilha Excel. Verifique se o arquivo está em formato válido."
        else:
            error_message = f"Erro interno: {error_type}. Verifique os logs do servidor para mais detalhes."
    else:
        error_message = f"Erro interno no servidor: {error_str} (Tipo: {error_type})"
    
    return JSONResponse(
        status_code=500,
        content={"detail": error_message}
    )

# Configuração para UTF-8
import sys
import locale
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def corrigir_encoding_json(dados):
    """Corrige encoding de caracteres especiais em dados JSON"""
    if isinstance(dados, dict):
        return {k: corrigir_encoding_json(v) for k, v in dados.items()}
    elif isinstance(dados, list):
        return [corrigir_encoding_json(item) for item in dados]
    elif isinstance(dados, str):
        # Corrige caracteres mal codificados
        correcoes = {
            '??': 'ã', '??': 'é', '??': 'í', '??': 'ó', '??': 'ú', '??': 'ç',
            '??': 'á', '??': 'ê', '??': 'ô', '??': 'õ', '??': 'à', '??': 'è',
            '??': 'ì', '??': 'ò', '??': 'ù', '??': 'ñ', '??': 'ü', '??': 'ä',
            '??': 'ö', '??': 'ß', '??': 'Ä', '??': 'Ö', '??': 'Ü'
        }
        texto_corrigido = dados
        for mal_codificado, correto in correcoes.items():
            texto_corrigido = texto_corrigido.replace(mal_codificado, correto)
        return texto_corrigido
    else:
        return dados

# ==================== SEGURANÇA E PERFORMANCE ====================

# Compressão GZip para melhor performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS - Configuração mais restritiva
# Em produção, usar variável de ambiente ALLOWED_ORIGINS
# Exemplo: ALLOWED_ORIGINS=https://www.absenteismocontroller.com.br,https://absenteismocontroller.com.br
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    # Separa por vírgula e remove espaços
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
else:
    # Desenvolvimento: permite todos (não usar em produção!)
    allowed_origins = ["*"] if os.getenv("ENVIRONMENT", "development") == "development" else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Content-Length"],
    max_age=3600,
)

# Rate Limiting - Proteção contra DDoS
rate_limit_store = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # 1 minuto
RATE_LIMIT_MAX_REQUESTS = 100  # Máximo de requisições por minuto

# Middleware de Logging de Requisições (primeiro)
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware de logging de requisições"""
    from .middleware_logging import request_logging_middleware
    return await request_logging_middleware(request, call_next)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Proteção contra abuso de requisições"""
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    
    # Limpa requisições antigas
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Verifica limite
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        # Log de segurança - rate limit excedido
        log_security(
            'rate_limit_exceeded',
            level='warning',
            ip_address=client_ip,
            details={
                'requests_count': len(rate_limit_store[client_ip]),
                'endpoint': str(request.url.path),
                'method': request.method
            }
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Muitas requisições. Tente novamente mais tarde."},
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
        )
    
    # Registra requisição
    rate_limit_store[client_ip].append(current_time)
    
    response = await call_next(request)
    return response

# Middleware de Headers de Segurança
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Adiciona headers de segurança essenciais"""
    response = await call_next(request)
    
    # Headers de Segurança
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # Content Security Policy (CSP) - Ajustar conforme necessário
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://cdnjs.cloudflare.com data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    response.headers["Content-Security-Policy"] = csp
    
    # HSTS (apenas em HTTPS)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    # Cache Control para recursos estáticos
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    
    # UTF-8
    if "Content-Type" in response.headers:
        if "charset" not in response.headers["Content-Type"].lower():
            response.headers["Content-Type"] += "; charset=utf-8"
    else:
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    
    return response

# Proteção contra acesso a arquivos sensíveis
SENSITIVE_PATTERNS = [
    ".env", ".git", ".gitignore", ".gitattributes",
    "__pycache__", ".pyc", ".pyo", ".pyd",
    ".sql", ".db", ".sqlite", ".sqlite3",
    "requirements.txt", "package.json", "package-lock.json",
    "docker-compose.yml", "Dockerfile", ".dockerignore",
    "README.md", "LICENSE", ".htaccess", ".htpasswd"
]

@app.middleware("http")
async def block_sensitive_files(request: Request, call_next):
    """Bloqueia acesso a arquivos sensíveis"""
    path = request.url.path.lower()
    
    # Verifica padrões sensíveis
    for pattern in SENSITIVE_PATTERNS:
        if pattern in path:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Acesso negado"}
            )
    
    # Bloqueia tentativas de path traversal
    if ".." in path or "//" in path:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Acesso negado"}
        )
    
    response = await call_next(request)
    return response

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
LOGOS_DIR = os.path.join(FRONTEND_DIR, "static", "logos")

def remover_logo_arquivo(caminho: Optional[str]):
    """Remove arquivo de logo do disco, se existir e estiver na pasta permitida."""
    if not caminho:
        return
    caminho_relativo = caminho.lstrip('/')
    arquivo_path = os.path.abspath(os.path.join(BASE_DIR, caminho_relativo.replace('/', os.sep)))
    logos_dir_abs = os.path.abspath(LOGOS_DIR)
    try:
        if os.path.commonpath([arquivo_path, logos_dir_abs]) != logos_dir_abs:
            return
    except ValueError:
        return
    if os.path.exists(arquivo_path):
        try:
            os.remove(arquivo_path)
        except OSError:
            pass

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

# ==================== HELPER FUNCTIONS ====================

def validar_client_id(db: Session, client_id: int) -> Client:
    """
    Valida se o client_id existe e retorna o cliente.
    Levanta HTTPException se não encontrar.
    
    IMPORTANTE: Esta função é crítica para LGPD - garante isolamento de dados.
    NUNCA retornar dados sem validar o client_id primeiro.
    """
    # Validação rigorosa de tipo e valor
    if not isinstance(client_id, int):
        raise HTTPException(
            status_code=400,
            detail="client_id deve ser um número inteiro"
        )
    
    if not client_id or client_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="client_id é obrigatório e deve ser maior que zero"
        )
    
    # Busca cliente no banco
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente com ID {client_id} não encontrado"
        )
    
    # Verifica se cliente está ativo (opcional, mas recomendado)
    if hasattr(client, 'situacao') and client.situacao and client.situacao.lower() != 'ativo':
        # Não bloqueia, apenas registra (pode ser necessário para histórico)
        pass
    
    return client

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Inicialização do sistema com logging"""
    app_logger.info("=" * 60)
    app_logger.info("INICIANDO SISTEMA - AbsenteismoController v2.0")
    app_logger.info("=" * 60)
    
    # Inicializa banco de dados
    app_logger.info("Inicializando banco de dados...")
    init_db()
    run_migrations()
    app_logger.info("Banco de dados inicializado com sucesso")
    
    # Cria pastas necessárias
    os.makedirs(LOGOS_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
    app_logger.info("Pastas do sistema criadas/verificadas")
    
    db = next(get_db())
    
    # Remove cliente fictício GrupoBiomed se existir (não cria mais automaticamente)
    from sqlalchemy import or_, func
    client_grupobiomed = db.query(Client).filter(
        or_(
            func.lower(Client.nome).like("%grupobiomed%"),
            func.lower(Client.nome_fantasia).like("%grupobiomed%"),
            Client.nome == "GrupoBiomed",
            Client.id == 1  # Remove também se for ID 1 (cliente padrão antigo)
        )
    ).first()
    if client_grupobiomed:
        # Deleta todos os dados relacionados primeiro
        from .models import Atestado, Upload, ClientLogo, ClientColumnMapping, SavedFilter
        for upload in client_grupobiomed.uploads:
            db.query(Atestado).filter(Atestado.upload_id == upload.id).delete()
        db.query(Upload).filter(Upload.client_id == client_grupobiomed.id).delete()
        db.query(ClientLogo).filter(ClientLogo.client_id == client_grupobiomed.id).delete()
        db.query(ClientColumnMapping).filter(ClientColumnMapping.client_id == client_grupobiomed.id).delete()
        db.query(SavedFilter).filter(SavedFilter.client_id == client_grupobiomed.id).delete()
        db.delete(client_grupobiomed)
        db.commit()
        app_logger.info("Cliente fictício GrupoBiomed removido permanentemente")
    
    # Cria usuário admin padrão se não existir
    admin = db.query(User).filter(User.username == "admin").first()
    admin_email = db.query(User).filter(User.email == "admin@grupobiomed.com").first()
    
    if not admin and not admin_email:
        admin = User(
            username="admin",
            email="admin@grupobiomed.com",
            password_hash=get_password_hash("admin123"),
            nome_completo="Administrador",
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        db.commit()
        app_logger.info("Usuário admin padrão criado")
        security_logger.warning("ATENÇÃO: Usuário admin padrão criado. Altere a senha!", extra={
            'username': 'admin',
            'default_password': True
        })
    else:
        app_logger.info("Usuário admin já existe")
    
    # Configurações padrão
    if not db.query(Config).filter(Config.chave == "nome_sistema").first():
        set_config_value(db, "nome_sistema", "AbsenteismoController", "Nome do sistema", "string")
        set_config_value(db, "empresa", "GrupoBiomed", "Nome da empresa", "string")
        set_config_value(db, "email_contato", "contato@grupobiomed.com", "Email de contato", "string")
        set_config_value(db, "tema_escuro", "false", "Tema escuro ativado", "boolean")
        set_config_value(db, "itens_por_pagina", "50", "Itens por página", "number")
        app_logger.info("Configurações padrão criadas")
    
    db.close()
    
    # Inicia sistema de backup automático
    try:
        from .backup_automatico import iniciar_backup_automatico
        iniciar_backup_automatico()
    except Exception as e:
        app_logger.warning(f"Erro ao iniciar backup automático: {e}")
    
    app_logger.info("=" * 60)
    app_logger.info("SISTEMA INICIADO COM SUCESSO")
    app_logger.info("=" * 60)

# ==================== ROUTES - FRONTEND ====================

@app.get("/landing", response_class=HTMLResponse)
async def landing_page():
    """Landing page - Página inicial"""
    file_path = os.path.join(FRONTEND_DIR, "landing.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Página de login"""
    file_path = os.path.join(FRONTEND_DIR, "login.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/configuracoes", response_class=HTMLResponse)
async def configuracoes_page():
    """Página de configurações"""
    file_path = os.path.join(FRONTEND_DIR, "configuracoes.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/download_app", response_class=HTMLResponse)
async def download_app_page():
    """Página de download do app desktop"""
    file_path = os.path.join(FRONTEND_DIR, "download_app.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/download/app")
async def download_app_file(current_user: User = Depends(get_current_active_user)):
    """Download do executável do app desktop"""
    app_dir = os.path.join(BASE_DIR, "app-desktop")
    exe_path = os.path.join(app_dir, "dist", "AbsenteismoController.exe")
    
    # Verifica se o executável existe
    if os.path.exists(exe_path):
        # Retorna o executável diretamente
        return FileResponse(
            exe_path,
            media_type='application/x-msdownload',
            filename='AbsenteismoController.exe',
            headers={
                'Content-Disposition': 'attachment; filename="AbsenteismoController.exe"'
            }
        )
    else:
        # Se não encontrar, retorna erro
        raise HTTPException(
            status_code=404, 
            detail="Executável não encontrado. O app ainda não foi compilado. Entre em contato com o administrador."
        )

@app.get("/", response_class=HTMLResponse)
async def index():
    """Página principal - Landing page"""
    file_path = os.path.join(FRONTEND_DIR, "landing.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Página principal - Dashboard"""
    file_path = os.path.join(FRONTEND_DIR, "index.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/upload", response_class=HTMLResponse)
async def upload_page():
    """Página de upload"""
    file_path = os.path.join(FRONTEND_DIR, "upload.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/preview", response_class=HTMLResponse)
async def preview_page():
    """Página de preview"""
    file_path = os.path.join(FRONTEND_DIR, "preview.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/analises", response_class=HTMLResponse)
async def analises_page():
    """Página de análises"""
    file_path = os.path.join(FRONTEND_DIR, "analises.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/tendencias", response_class=HTMLResponse)
async def tendencias_page():
    """Página de tendências"""
    file_path = os.path.join(FRONTEND_DIR, "tendencias.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Rota de relatórios removida - exportação agora está na apresentação
# @app.get("/relatorios", response_class=HTMLResponse)
# async def relatorios_page():
#     """Página de relatórios"""
#     file_path = os.path.join(FRONTEND_DIR, "relatorios.html")
#     with open(file_path, "r", encoding="utf-8") as f:
#         return HTMLResponse(content=f.read())

@app.get("/apresentacao", response_class=HTMLResponse)
async def apresentacao_page():
    """Página de apresentação"""
    file_path = os.path.join(FRONTEND_DIR, "apresentacao.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/funcionarios", response_class=HTMLResponse)
async def funcionarios_page():
    """Página de funcionários"""
    file_path = os.path.join(FRONTEND_DIR, "funcionarios.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/comparativos", response_class=HTMLResponse)
async def comparativos_page():
    """Página de comparativos"""
    file_path = os.path.join(FRONTEND_DIR, "comparativos.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/dados_powerbi", response_class=HTMLResponse)
async def dados_powerbi_page():
    """Página de análise de dados estilo PowerBI"""
    file_path = os.path.join(FRONTEND_DIR, "dados_powerbi.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/produtividade", response_class=HTMLResponse)
async def produtividade_page():
    """Página de produtividade"""
    file_path = os.path.join(FRONTEND_DIR, "produtividade.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/upload_inteligente", response_class=HTMLResponse)
async def upload_inteligente_page():
    """Página de upload inteligente"""
    file_path = os.path.join(FRONTEND_DIR, "upload_inteligente.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/dashboard_powerbi", response_class=HTMLResponse)
async def dashboard_powerbi_page():
    """Página do Dashboard PowerBI"""
    file_path = os.path.join(FRONTEND_DIR, "dashboard_powerbi.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/auto_processor", response_class=HTMLResponse)
async def auto_processor_page():
    """Página do Sistema Automático"""
    file_path = os.path.join(FRONTEND_DIR, "auto_processor.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ==================== ROUTES - API ====================

@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check completo - verifica saúde do sistema
    Essencial para monitoramento e auditoria ISO 27001
    """
    import psutil
    import shutil
    
    health_status = {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Verifica banco de dados
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
        health_status["checks"]["database"] = {
            "status": "ok",
            "message": "Conexão com banco de dados funcionando"
        }
    except Exception as e:
        db_status = "error"
        health_status["checks"]["database"] = {
            "status": "error",
            "message": f"Erro na conexão com banco: {str(e)}"
        }
        health_status["status"] = "unhealthy"
        log_error(e, {"check": "database"})
    
    # Verifica integridade do banco (SQLite)
    try:
        result = db.execute(text("PRAGMA integrity_check"))
        integrity_result = result.scalar()
        if integrity_result == "ok":
            health_status["checks"]["database_integrity"] = {
                "status": "ok",
                "message": "Integridade do banco verificada"
            }
        else:
            health_status["checks"]["database_integrity"] = {
                "status": "warning",
                "message": f"Problemas detectados: {integrity_result}"
            }
            health_status["status"] = "degraded"
            app_logger.warning(f"Integridade do banco: {integrity_result}")
    except Exception as e:
        health_status["checks"]["database_integrity"] = {
            "status": "error",
            "message": f"Erro ao verificar integridade: {str(e)}"
        }
        log_error(e, {"check": "database_integrity"})
    
    # Verifica espaço em disco
    try:
        disk_usage = shutil.disk_usage(BASE_DIR)
        total_gb = disk_usage.total / (1024**3)
        free_gb = disk_usage.free / (1024**3)
        used_percent = (disk_usage.used / disk_usage.total) * 100
        
        disk_status = "ok" if used_percent < 90 else "warning" if used_percent < 95 else "error"
        if disk_status != "ok":
            health_status["status"] = "degraded" if disk_status == "warning" else "unhealthy"
        
        health_status["checks"]["disk"] = {
            "status": disk_status,
            "total_gb": round(total_gb, 2),
            "free_gb": round(free_gb, 2),
            "used_percent": round(used_percent, 2),
            "message": f"{round(used_percent, 1)}% usado"
        }
    except Exception as e:
        health_status["checks"]["disk"] = {
            "status": "error",
            "message": f"Erro ao verificar disco: {str(e)}"
        }
        log_error(e, {"check": "disk"})
    
    # Verifica memória
    try:
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_status = "ok" if memory_percent < 85 else "warning" if memory_percent < 95 else "error"
        if memory_status != "ok":
            health_status["status"] = "degraded" if memory_status == "warning" else "unhealthy"
        
        health_status["checks"]["memory"] = {
            "status": memory_status,
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_percent": round(memory_percent, 2),
            "message": f"{round(memory_percent, 1)}% usado"
        }
    except Exception as e:
        health_status["checks"]["memory"] = {
            "status": "error",
            "message": f"Erro ao verificar memória: {str(e)}"
        }
        log_error(e, {"check": "memory"})
    
    # Verifica pastas críticas
    try:
        critical_paths = {
            "database": os.path.join(BASE_DIR, "database"),
            "uploads": UPLOADS_DIR,
            "exports": EXPORTS_DIR,
            "logs": os.path.join(BASE_DIR, "logs")
        }
        
        paths_status = {}
        for name, path in critical_paths.items():
            if os.path.exists(path):
                paths_status[name] = {"status": "ok", "path": path}
            else:
                paths_status[name] = {"status": "error", "path": path, "message": "Pasta não existe"}
                health_status["status"] = "unhealthy"
        
        health_status["checks"]["paths"] = paths_status
    except Exception as e:
        health_status["checks"]["paths"] = {
            "status": "error",
            "message": f"Erro ao verificar pastas: {str(e)}"
        }
        log_error(e, {"check": "paths"})
    
    # Log do health check
    if health_status["status"] != "healthy":
        app_logger.warning(f"Health check: {health_status['status']}", extra=health_status["checks"])
    else:
        app_logger.info("Health check: sistema saudável")
    
    return health_status

# ==================== AUTHENTICATION API ====================

@app.post("/api/auth/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db),
    request: Request = None
):
    """Login de usuário"""
    start_time = time.time()
    client_ip = request.client.host if request and request.client else "unknown"
    
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            # Log de tentativa de login falhada (segurança)
            log_security(
                'failed_login',
                level='warning',
                ip_address=client_ip,
                details={'username': form_data.username}
            )
            raise HTTPException(
                status_code=401,
                detail="Usuário ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Log de login bem-sucedido (auditoria)
        duration_ms = (time.time() - start_time) * 1000
        log_audit(
            action='login',
            user_id=user.id,
            ip_address=client_ip,
            details={'username': user.username, 'duration_ms': duration_ms}
        )
        
        app_logger.info(f"Login bem-sucedido: {user.username} (IP: {client_ip})")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "nome_completo": user.nome_completo,
                "is_admin": user.is_admin
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, {'operation': 'login', 'username': form_data.username, 'ip': client_ip})
        raise HTTPException(status_code=500, detail="Erro interno ao processar login")

@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Retorna informações do usuário atual"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "nome_completo": current_user.nome_completo,
        "is_admin": current_user.is_admin,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }

@app.post("/api/auth/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout (client-side deve remover o token)"""
    return {"message": "Logout realizado com sucesso"}

# ==================== CONFIGURATIONS API ====================

@app.get("/api/config")
async def get_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retorna todas as configurações"""
    configs = db.query(Config).all()
    result = {}
    for config in configs:
        result[config.chave] = {
            "valor": get_config_value(db, config.chave),
            "tipo": config.tipo,
            "descricao": config.descricao
        }
    return result

@app.get("/api/config/{chave}")
async def get_config_value_api(
    chave: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retorna valor de uma configuração específica"""
    valor = get_config_value(db, chave)
    return {"chave": chave, "valor": valor}

@app.put("/api/config/{chave}")
async def update_config(
    chave: str,
    valor: str = Form(...),
    descricao: str = Form(None),
    tipo: str = Form("string"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Atualiza uma configuração (apenas admin)"""
    set_config_value(db, chave, valor, descricao, tipo)
    return {"message": f"Configuração {chave} atualizada com sucesso"}

# ==================== USERS API ====================

@app.get("/api/users")
async def list_users(current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    """Lista todos os usuários (apenas admin)"""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "nome_completo": u.nome_completo,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None
        }
        for u in users
    ]

@app.post("/api/users")
async def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    nome_completo: str = Form(None),
    is_admin: bool = Form(False),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Cria novo usuário (apenas admin)"""
    # Verifica se usuário já existe
    existing = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Usuário ou email já existe")
    
    user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        nome_completo=nome_completo,
        is_admin=is_admin,
        is_active=True
    )
    db.add(user)
    db.commit()
    return {"message": "Usuário criado com sucesso", "user_id": user.id}

@app.put("/api/users/{user_id}")
async def update_user(
    user_id: int,
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    nome_completo: Optional[str] = Form(None),
    is_admin: Optional[bool] = Form(None),
    is_active: Optional[bool] = Form(None),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Atualiza usuário (apenas admin)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Não permite editar a si mesmo (proteção)
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Não é possível editar seu próprio usuário")
    
    # Atualiza campos se fornecidos
    if username is not None:
        # Verifica se username já existe em outro usuário
        existing = db.query(User).filter(
            User.username == username,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username já existe")
        user.username = username
    
    if email is not None:
        # Verifica se email já existe em outro usuário
        existing = db.query(User).filter(
            User.email == email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email já existe")
        user.email = email
    
    if password is not None and password.strip():
        user.password_hash = get_password_hash(password)
    
    if nome_completo is not None:
        user.nome_completo = nome_completo
    
    if is_admin is not None:
        user.is_admin = is_admin
    
    if is_active is not None:
        user.is_active = is_active
    
    db.commit()
    return {"message": "Usuário atualizado com sucesso"}

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    client_id: int = Form(...),  # Obrigatório, sem valor padrão
    mes_referencia: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    request: Request = None,
    current_user: User = Depends(get_current_active_user)
):
    """Upload de planilha"""
    start_time = time.time()
    client_ip = request.client.host if request and request.client else "unknown"
    
    try:
        # Log de início da operação
        # Nota: 'filename' é campo reservado do LogRecord, usar 'file_name' ao invés
        app_logger.info(f"Iniciando upload de planilha para cliente {client_id}", extra={
            'user_id': current_user.id,
            'client_id': client_id,
            'file_name': file.filename,  # Renomeado de 'filename' para evitar conflito
            'ip_address': client_ip
        })
        
        # Valida se o cliente existe
        client = validar_client_id(db, client_id)
        
        # Auditoria - upload iniciado
        log_audit(
            action='upload_file_start',
            user_id=current_user.id,
            client_id=client_id,
            resource='upload',
            ip_address=client_ip,
            details={'file_name': file.filename, 'mes_referencia': mes_referencia}  # Renomeado de 'filename' para evitar conflito
        )
        
        # Valida se o arquivo foi enviado
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="Nenhum arquivo foi enviado")
        
        # Valida extensão do arquivo
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Formato de arquivo inválido. Use .xlsx ou .xls")
        
        # Verifica se o diretório de uploads existe e tem permissão
        try:
            os.makedirs(UPLOADS_DIR, exist_ok=True)
            # Testa se consegue escrever no diretório
            test_file = os.path.join(UPLOADS_DIR, '.test_write')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro de permissão no diretório de uploads: {str(e)}"
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao acessar diretório de uploads: {str(e)}"
            )
        
        # Salva arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOADS_DIR, saved_filename)
        
        try:
            with open(file_path, "wb") as buffer:
                # Lê o conteúdo do arquivo
                content = await file.read()
                buffer.write(content)
        except Exception as e:
            # Remove arquivo parcial se existir
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao salvar arquivo: {str(e)}"
            )
        
        # Verifica se o arquivo foi salvo corretamente
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=500,
                detail="Arquivo não foi salvo corretamente. Tente novamente."
            )
        
        # Busca mapeamento customizado do cliente (se existir)
        custom_mapping = None
        mapping_obj = db.query(ClientColumnMapping).filter(ClientColumnMapping.client_id == client_id).first()
        if mapping_obj and mapping_obj.column_mapping:
            try:
                mapping_data = json.loads(mapping_obj.column_mapping)
                # O mapeamento pode estar dentro de um objeto com 'column_mapping' ou ser o próprio dicionário
                if isinstance(mapping_data, dict) and 'column_mapping' in mapping_data:
                    custom_mapping = mapping_data['column_mapping']
                elif isinstance(mapping_data, dict):
                    custom_mapping = mapping_data
                else:
                    custom_mapping = None
                
                print(f"📋 Mapeamento carregado para cliente {client_id}: {custom_mapping}")
            except Exception as e:
                print(f"❌ Erro ao carregar mapeamento: {e}")
                custom_mapping = None
        
        # Processa Excel
        try:
            processor = ExcelProcessor(file_path, custom_mapping=custom_mapping)
            registros = processor.processar()
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=f"Erro ao processar planilha Excel: {str(e)}")
        
        if not registros:
            raise HTTPException(status_code=400, detail="Erro ao processar planilha. A planilha não contém dados válidos ou está vazia.")
        
        # Usa o mês de referência fornecido pelo usuário, ou tenta detectar automaticamente
        mes_ref = None
        
        if mes_referencia:
            # Valida formato do mês de referência (YYYY-MM)
            try:
                # Valida se está no formato correto
                if len(mes_referencia) == 7 and mes_referencia[4] == '-':
                    ano, mes = mes_referencia.split('-')
                    if int(ano) >= 2020 and int(ano) <= 2100 and int(mes) >= 1 and int(mes) <= 12:
                        mes_ref = mes_referencia
                    else:
                        raise HTTPException(status_code=400, detail="Formato de mês de referência inválido. Use YYYY-MM (ex: 2025-10)")
                else:
                    raise HTTPException(status_code=400, detail="Formato de mês de referência inválido. Use YYYY-MM (ex: 2025-10)")
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de mês de referência inválido. Use YYYY-MM (ex: 2025-10)")
        
        # Se não foi fornecido, tenta detectar automaticamente (fallback)
        if not mes_ref:
            campos_data = ['data_afastamento', 'data_retorno', 'DATA_AFASTAMENTO', 'DATA_RETORNO']
            
            for reg in registros[:10]:  # Verifica os primeiros 10 registros
                for campo in campos_data:
                    if campo in reg and reg[campo]:
                        data = reg[campo]
                        if isinstance(data, datetime):
                            mes_ref = data.strftime("%Y-%m")
                            break
                        elif isinstance(data, str):
                            try:
                                data_obj = datetime.strptime(data[:10], "%Y-%m-%d")
                                mes_ref = data_obj.strftime("%Y-%m")
                                break
                            except:
                                pass
                if mes_ref:
                    break
            
            # Se não encontrou, usa o mês atual
            if not mes_ref:
                mes_ref = datetime.now().strftime("%Y-%m")
        
        # Cria registro de upload
        upload = Upload(
            client_id=client_id,
            filename=saved_filename,
            mes_referencia=mes_ref,
            total_registros=len(registros)
        )
        db.add(upload)
        db.flush()
        
        # Salva atestados - filtra apenas campos válidos do modelo
        campos_validos = {
            'nomecompleto', 'descricao_atestad', 'dias_atestados', 'cid', 'diagnostico',
            'centro_custo', 'setor', 'motivo_atestado', 'escala', 'horas_dia', 'horas_perdi',
            'nome_funcionario', 'cpf', 'matricula', 'cargo', 'genero', 'data_afastamento',
            'data_retorno', 'tipo_info_atestado', 'tipo_atestado', 'descricao_cid',
            'numero_dias_atestado', 'numero_horas_atestado', 'dias_perdidos', 'horas_perdidas',
            'dados_originais'
        }
        
        for idx, reg in enumerate(registros):
            try:
                # Filtra apenas campos válidos do modelo
                reg_filtrado = {k: v for k, v in reg.items() if k in campos_validos}
                
                # Converte tipos de dados para evitar erros
                # Converte datas de string/datetime para date se necessário
                from datetime import date as date_type
                
                if 'data_afastamento' in reg_filtrado and reg_filtrado['data_afastamento']:
                    try:
                        if isinstance(reg_filtrado['data_afastamento'], str):
                            dt = datetime.strptime(reg_filtrado['data_afastamento'][:10], "%Y-%m-%d")
                            reg_filtrado['data_afastamento'] = dt.date()
                        elif isinstance(reg_filtrado['data_afastamento'], datetime):
                            reg_filtrado['data_afastamento'] = reg_filtrado['data_afastamento'].date()
                        elif isinstance(reg_filtrado['data_afastamento'], date_type):
                            pass  # Já é date
                        else:
                            reg_filtrado['data_afastamento'] = None
                    except:
                        reg_filtrado['data_afastamento'] = None
                else:
                    reg_filtrado['data_afastamento'] = None
                
                if 'data_retorno' in reg_filtrado and reg_filtrado['data_retorno']:
                    try:
                        if isinstance(reg_filtrado['data_retorno'], str):
                            dt = datetime.strptime(reg_filtrado['data_retorno'][:10], "%Y-%m-%d")
                            reg_filtrado['data_retorno'] = dt.date()
                        elif isinstance(reg_filtrado['data_retorno'], datetime):
                            reg_filtrado['data_retorno'] = reg_filtrado['data_retorno'].date()
                        elif isinstance(reg_filtrado['data_retorno'], date_type):
                            pass  # Já é date
                        else:
                            reg_filtrado['data_retorno'] = None
                    except:
                        reg_filtrado['data_retorno'] = None
                else:
                    reg_filtrado['data_retorno'] = None
                
                # Garante que valores numéricos são float ou None
                for campo_num in ['dias_atestados', 'horas_dia', 'horas_perdi', 'numero_dias_atestado', 
                                 'numero_horas_atestado', 'dias_perdidos', 'horas_perdidas']:
                    if campo_num in reg_filtrado:
                        if reg_filtrado[campo_num] is None:
                            reg_filtrado[campo_num] = 0.0
                        else:
                            try:
                                reg_filtrado[campo_num] = float(reg_filtrado[campo_num])
                            except:
                                reg_filtrado[campo_num] = 0.0
                
                # Garante que tipo_info_atestado é int ou None
                if 'tipo_info_atestado' in reg_filtrado and reg_filtrado['tipo_info_atestado'] is not None:
                    try:
                        reg_filtrado['tipo_info_atestado'] = int(reg_filtrado['tipo_info_atestado'])
                    except:
                        reg_filtrado['tipo_info_atestado'] = None
                
                # Garante que dados_originais é string JSON válida ou None
                if 'dados_originais' in reg_filtrado:
                    dados_orig = reg_filtrado['dados_originais']
                    if dados_orig is not None:
                        # Se já é string, verifica se é JSON válido
                        if isinstance(dados_orig, str):
                            try:
                                # Valida se é JSON válido
                                json.loads(dados_orig)
                                # Se passou, mantém como está
                            except (json.JSONDecodeError, TypeError):
                                # Se não for JSON válido, tenta converter dict para JSON
                                try:
                                    if isinstance(dados_orig, dict):
                                        reg_filtrado['dados_originais'] = json.dumps(dados_orig, ensure_ascii=False, default=str)
                                    else:
                                        reg_filtrado['dados_originais'] = None
                                except:
                                    reg_filtrado['dados_originais'] = None
                        elif isinstance(dados_orig, dict):
                            # Se for dict, converte para JSON string
                            try:
                                reg_filtrado['dados_originais'] = json.dumps(dados_orig, ensure_ascii=False, default=str)
                            except:
                                reg_filtrado['dados_originais'] = None
                        else:
                            reg_filtrado['dados_originais'] = None
                    else:
                        reg_filtrado['dados_originais'] = None
                
                atestado = Atestado(
                    upload_id=upload.id,
                    **reg_filtrado
                )
                db.add(atestado)
            except Exception as e:
                # Log do erro mas continua processando outros registros
                print(f"Erro ao processar registro {idx + 1}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        db.commit()
        
        # Log de sucesso
        duration_ms = (time.time() - start_time) * 1000
        log_operation(
            operation='upload_file',
            status='success',
            duration_ms=duration_ms,
            user_id=current_user.id,
            client_id=client_id,
            details={
                'upload_id': upload.id,
                'total_registros': len(registros),
                'mes_referencia': mes_ref,
                'file_name': file.filename  # Renomeado de 'filename' para evitar conflito
            }
        )
        
        # Auditoria - upload concluído
        log_audit(
            action='upload_file_complete',
            user_id=current_user.id,
            client_id=client_id,
            resource='upload',
            ip_address=client_ip,
            details={
                'upload_id': upload.id,
                'total_registros': len(registros),
                'mes_referencia': mes_ref,
                'duration_ms': duration_ms
            }
        )
        
        app_logger.info(f"Upload concluído: {len(registros)} registros processados para cliente {client_id} em {duration_ms:.2f}ms")
        
        return {
            "success": True,
            "upload_id": upload.id,
            "total_registros": len(registros),
            "mes_referencia": mes_ref
        }
    
    except HTTPException as e:
        db.rollback()
        duration_ms = (time.time() - start_time) * 1000
        log_operation(
            operation='upload_file',
            status='failed',
            duration_ms=duration_ms,
            user_id=current_user.id if 'current_user' in locals() else None,
            client_id=client_id,
            details={'error': str(e.detail), 'status_code': e.status_code}
        )
        raise
    except Exception as e:
        db.rollback()
        duration_ms = (time.time() - start_time) * 1000
        
        # Captura traceback completo para debug
        import traceback
        error_traceback = traceback.format_exc()
        
        # Log de erro detalhado - com tratamento para evitar erro no logger
        try:
            log_error(
                e,
                context={
                    'operation': 'upload_file',
                    'file_name': file.filename if 'file' in locals() and file else None,
                    'duration_ms': duration_ms,
                    'error_traceback': error_traceback  # Renomeado de 'traceback' para evitar conflito
                },
                user_id=current_user.id if 'current_user' in locals() else None,
                client_id=client_id if 'client_id' in locals() else None
            )
        except Exception as log_err:
            # Se o log falhar, pelo menos registra no console
            print(f"\n{'='*60}")
            print(f"ERRO AO TENTAR LOGAR (ignorado): {log_err}")
            print(f"ERRO ORIGINAL NO UPLOAD:")
            print(f"Tipo: {type(e).__name__}")
            print(f"Mensagem: {str(e)}")
            print(f"{'='*60}\n")
        
        # Log completo no console para debug (sempre funciona)
        try:
            app_logger.error(f"Erro ao processar upload: {str(e)}", exc_info=True)
        except:
            pass  # Se falhar, ignora
        
        print(f"\n{'='*60}")
        print(f"ERRO NO UPLOAD:")
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensagem: {str(e)}")
        print(f"Traceback completo:")
        print(error_traceback)
        print(f"{'='*60}\n")
        
        # Retorna mensagem mais específica baseada no tipo de erro
        error_message = "Erro ao processar planilha. Verifique o formato do arquivo e tente novamente."
        
        error_str = str(e).lower()
        error_type = type(e).__name__
        
        # Mensagens específicas por tipo de erro
        if "permission" in error_str or "acesso" in error_str or "denied" in error_str or "PermissionError" in error_type:
            error_message = "Erro de permissão ao acessar o arquivo. Verifique as permissões do sistema."
        elif "no such file" in error_str or "arquivo não encontrado" in error_str or "FileNotFoundError" in error_type:
            error_message = "Arquivo não encontrado. Verifique se o arquivo foi enviado corretamente."
        elif "decode" in error_str or "encoding" in error_str or "codificação" in error_str or "UnicodeDecodeError" in error_type:
            error_message = "Erro de codificação no arquivo. Certifique-se de que o arquivo está em formato Excel válido."
        elif "database" in error_str or "sql" in error_str or "banco" in error_str or "IntegrityError" in error_type or "OperationalError" in error_type:
            error_message = "Erro ao salvar no banco de dados. Tente novamente ou entre em contato com o suporte."
        elif "authentication" in error_str or "token" in error_str or "login" in error_str:
            error_message = "Erro de autenticação. Faça login novamente."
        elif "client" in error_str or "cliente" in error_str or "client_id" in error_str:
            error_message = f"Erro relacionado ao cliente: {str(e)}"
        elif "json" in error_str or "JSONDecodeError" in error_type or "serialize" in error_str:
            error_message = "Erro ao processar dados da planilha. Verifique se o arquivo não está corrompido."
        elif "pandas" in error_str or "excel" in error_str or "read_excel" in error_str:
            error_message = "Erro ao ler arquivo Excel. Verifique se o arquivo está em formato .xlsx ou .xls válido."
        elif "memory" in error_str or "MemoryError" in error_type:
            error_message = "Arquivo muito grande. Tente dividir a planilha em partes menores."
        else:
            # Para debug, inclui mais detalhes
            if os.getenv("ENVIRONMENT", "development") == "development":
                error_message = f"Erro ao processar upload: {str(e)} (Tipo: {error_type})"
            else:
                error_message = f"Erro ao processar planilha: {str(e)[:100]}"
        
        # Garante que a mensagem de erro seja retornada corretamente
        raise HTTPException(
            status_code=500, 
            detail=error_message
        )

@app.get("/api/uploads")
async def list_uploads(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista uploads"""
    # Valida client_id
    validar_client_id(db, client_id)
    
    uploads = db.query(Upload).filter(Upload.client_id == client_id).order_by(Upload.data_upload.desc()).all()
    
    return [
        {
            "id": u.id,
            "filename": u.filename,
            "mes_referencia": u.mes_referencia,
            "data_upload": u.data_upload.isoformat(),
            "total_registros": u.total_registros
        }
        for u in uploads
    ]

@app.get("/api/dashboard")
async def dashboard(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    funcionario: Optional[List[str]] = Query(None),
    setor: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    request: Request = None,
    current_user: User = Depends(get_current_active_user)
):
    """Dashboard principal"""
    start_time = time.time()
    client_ip = request.client.host if request and request.client else "unknown"
    
    try:
        # Valida client_id (crítico para LGPD)
        client = validar_client_id(db, client_id)
        
        # Log de acesso ao dashboard (auditoria LGPD)
        app_logger.info(f"Acesso ao dashboard - Cliente: {client_id}, Usuário: {current_user.id}")
        
        analytics = Analytics(db)
        insights_engine = InsightsEngine(db)
        
        # Trata cada métrica individualmente para não quebrar tudo se uma falhar
        try:
            metricas = analytics.metricas_gerais(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular métricas gerais: {e}")
            metricas = {
                "total_atestados_dias": 0,
                "total_dias_perdidos": 0,
                "total_horas_perdidas": 0
            }
        
        try:
            top_cids = analytics.top_cids(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular top CIDs: {e}")
            top_cids = []
        
        try:
            top_setores = analytics.top_setores(client_id, 5, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular top setores: {e}")
            top_setores = []
        
        try:
            evolucao = analytics.evolucao_mensal(client_id, 12, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular evolução mensal: {e}")
            evolucao = []
        
        # Calcula variações mês a mês (dias/horas) para análises comparativas
        variacao_mensal = []
        if evolucao:
            anterior = None
            for item in evolucao:
                current_dias = float(item.get('dias_perdidos') or 0)
                current_horas = float(item.get('horas_perdidas') or 0)
                registro = {
                    "mes": item.get('mes'),
                    "dias": round(current_dias, 2),
                    "horas": round(current_horas, 2),
                    "variacao_dias": 0.0,
                    "variacao_horas": 0.0,
                    "percentual_dias": None,
                    "percentual_horas": None
                }
                
                if anterior:
                    variacao_dias = current_dias - anterior.get('dias_perdidos', 0)
                    variacao_horas = current_horas - anterior.get('horas_perdidas', 0)
                    registro["variacao_dias"] = round(variacao_dias, 2)
                    registro["variacao_horas"] = round(variacao_horas, 2)
                    registro["percentual_dias"] = round(((variacao_dias / anterior.get('dias_perdidos', 1)) * 100), 2) if anterior.get('dias_perdidos') else None
                    registro["percentual_horas"] = round(((variacao_horas / anterior.get('horas_perdidas', 1)) * 100), 2) if anterior.get('horas_perdidas') else None
                else:
                    registro["variacao_dias"] = 0.0
                    registro["variacao_horas"] = 0.0
                
                variacao_mensal.append(registro)
                anterior = {
                    'dias_perdidos': current_dias,
                    'horas_perdidas': current_horas
                }
        
        try:
            distribuicao_genero = analytics.distribuicao_genero_funcionarios(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular distribuição de gênero: {e}")
            distribuicao_genero = []
        
        try:
            genero_mensal = analytics.distribuicao_genero_mensal(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular distribuição mensal por gênero: {e}")
            genero_mensal = []
        
        try:
            top_funcionarios = analytics.top_funcionarios(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular top funcionários: {e}")
            top_funcionarios = []
        
        try:
            top_escalas = analytics.top_escalas(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular top escalas: {e}")
            top_escalas = []
        
        try:
            top_motivos = analytics.top_motivos(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular top motivos: {e}")
            top_motivos = []
        
        try:
            dias_centro_custo = analytics.dias_perdidos_por_centro_custo(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular dias por centro de custo: {e}")
            dias_centro_custo = []
        
        try:
            distribuicao_dias = analytics.distribuicao_dias_por_atestado(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular distribuição de dias: {e}")
            distribuicao_dias = []
        
        try:
            media_cid = analytics.media_dias_por_cid(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            app_logger.warning(f"Erro ao calcular média por CID para cliente {client_id}: {e}", extra={'client_id': client_id})
            media_cid = []
        
        try:
            evolucao_setor = analytics.evolucao_por_setor(client_id, 12, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            app_logger.warning(f"Erro ao calcular evolução por setor para cliente {client_id}: {e}", extra={'client_id': client_id})
            evolucao_setor = {}
        
        try:
            comparativo_dias_horas = analytics.comparativo_dias_horas(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            app_logger.warning(f"Erro ao calcular comparativo dias/horas para cliente {client_id}: {e}", extra={'client_id': client_id})
            comparativo_dias_horas = []
        
        try:
            frequencia_atestados = analytics.frequencia_atestados_por_funcionario(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            app_logger.warning(f"Erro ao calcular frequência de atestados para cliente {client_id}: {e}", extra={'client_id': client_id})
            frequencia_atestados = []
        
        try:
            dias_setor_genero = analytics.dias_perdidos_setor_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            app_logger.warning(f"Erro ao calcular dias por setor e gênero para cliente {client_id}: {e}", extra={'client_id': client_id})
            dias_setor_genero = []
        
        try:
            insights = insights_engine.gerar_insights(client_id)
        except Exception as e:
            app_logger.error(f"Erro ao gerar insights para cliente {client_id}: {e}", exc_info=True, extra={'client_id': client_id})
            insights = []
        
        # Busca alertas
        try:
            alertas_system = AlertasSystem(db)
            alertas = alertas_system.detectar_alertas(client_id, mes_inicio, mes_fim)
        except Exception as e:
            app_logger.warning(f"Erro ao detectar alertas para cliente {client_id}: {e}", extra={'client_id': client_id})
            alertas = []
        
        # Busca dados de produtividade (todos os meses)
        try:
            produtividade_data = db.query(Produtividade).filter(
                Produtividade.client_id == client_id
            ).order_by(Produtividade.mes_referencia.desc(), Produtividade.numero_tipo).all()
            
            produtividade = []
            if produtividade_data:
                # Retorna todos os meses para o gráfico poder somar corretamente
                produtividade = [
                    {
                        "numero_tipo": p.numero_tipo,
                        "tipo_consulta": p.tipo_consulta,
                        "ocupacionais": p.ocupacionais or 0,
                        "assistenciais": p.assistenciais or 0,
                        "acidente_trabalho": p.acidente_trabalho or 0,
                        "inss": p.inss or 0,
                        "sinistralidade": p.sinistralidade or 0,
                        "absenteismo": p.absenteismo or 0,
                        "pericia_indireta": p.pericia_indireta or 0,
                        "total": p.total or 0,
                        "mes_referencia": p.mes_referencia
                    }
                    for p in produtividade_data
                ]
        except Exception as e:
            app_logger.warning(f"Erro ao buscar produtividade para cliente {client_id}: {e}", extra={'client_id': client_id})
            produtividade = []
        
        # Busca campos disponíveis do cliente (mapeamento)
        campos_disponiveis = {}
        try:
            mapping_obj = db.query(ClientColumnMapping).filter(ClientColumnMapping.client_id == client_id).first()
            if mapping_obj and mapping_obj.column_mapping:
                try:
                    mapping_data = json.loads(mapping_obj.column_mapping)
                    if isinstance(mapping_data, dict) and 'column_mapping' in mapping_data:
                        campos_disponiveis = mapping_data.get('column_mapping', {})
                    elif isinstance(mapping_data, dict):
                        campos_disponiveis = mapping_data
                except:
                    pass
        except Exception as e:
            app_logger.warning(f"Erro ao buscar campos disponíveis para cliente {client_id}: {e}", extra={'client_id': client_id})
        
        # Verifica quais campos realmente têm dados no banco
        campos_com_dados = {}
        try:
            # Busca uma amostra de registros para verificar campos preenchidos
            amostra = db.query(Atestado).join(Upload).filter(
                Upload.client_id == client_id
            ).limit(100).all()
            
            if amostra:
                # Campos do modelo que podem ter dados
                campos_modelo = [
                    'nomecompleto', 'cpf', 'matricula', 'setor', 'centro_custo', 'cargo',
                    'genero', 'data_afastamento', 'data_retorno', 'cid', 'diagnostico',
                    'descricao_cid', 'dias_atestados', 'horas_perdi', 'motivo_atestado',
                    'escala', 'tipo_atestado', 'descricao_atestad'
                ]
                
                for campo in campos_modelo:
                    # Verifica se pelo menos um registro tem esse campo preenchido
                    tem_dados = any(
                        getattr(reg, campo, None) not in (None, '', 0, 0.0) 
                        for reg in amostra
                    )
                    if tem_dados:
                        campos_com_dados[campo] = True
        except Exception as e:
            print(f"Erro ao verificar campos com dados: {e}")
        
        # Dados específicos para Roda de Ouro (APENAS para client_id = 4)
        classificacao_funcionarios_ro = []
        classificacao_setores_ro = []
        classificacao_doencas_ro = []
        dias_ano_coerencia = {'anos': [], 'coerente': [], 'sem_coerencia': []}
        analise_coerencia = {'coerente': 0, 'sem_coerencia': 0, 'total': 0, 'percentual_coerente': 0, 'percentual_sem_coerencia': 0}
        tempo_servico_atestados = []
        
        # Novas análises de horas e gênero (especialmente para Roda de Ouro)
        horas_perdidas_genero = []
        horas_perdidas_setor = []
        evolucao_mensal_horas = []
        analise_detalhada_genero_data = {}
        comparativo_dias_horas_genero_data = []
        horas_perdidas_setor_genero_data = []
        
        # Só calcula se for Roda de Ouro (ID = 4)
        if client_id == 4:
            try:
                classificacao_funcionarios_ro = analytics.classificacao_funcionarios_roda_ouro(client_id, 15, mes_inicio, mes_fim, funcionario, setor)
            except Exception as e:
                print(f"Erro ao calcular classificação funcionários RO: {e}")
            
            try:
                classificacao_setores_ro = analytics.classificacao_setores_roda_ouro(client_id, 15, mes_inicio, mes_fim, funcionario, setor)
                print(f"✅ Classificação Setores RO retornou {len(classificacao_setores_ro)} registros")
            except Exception as e:
                print(f"❌ Erro ao calcular classificação setores RO: {e}")
                import traceback
                traceback.print_exc()
                classificacao_setores_ro = []
            
            try:
                classificacao_doencas_ro = analytics.classificacao_doencas_roda_ouro(client_id, 15, mes_inicio, mes_fim, funcionario, setor)
            except Exception as e:
                print(f"Erro ao calcular classificação doenças RO: {e}")
            
            try:
                dias_ano_coerencia = analytics.dias_atestados_por_ano_coerencia(client_id, mes_inicio, mes_fim, funcionario, setor)
            except Exception as e:
                print(f"Erro ao calcular dias por ano coerência: {e}")
            
            try:
                analise_coerencia = analytics.analise_atestados_coerencia(client_id, mes_inicio, mes_fim, funcionario, setor)
            except Exception as e:
                print(f"Erro ao calcular análise coerência: {e}")
            
            try:
                tempo_servico_atestados = analytics.tempo_servico_atestados(client_id, mes_inicio, mes_fim, funcionario, setor)
            except Exception as e:
                print(f"Erro ao calcular tempo serviço: {e}")
            
            # Novas análises de horas e gênero
            try:
                horas_perdidas_genero = analytics.horas_perdidas_por_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
            except Exception as e:
                print(f"Erro ao calcular horas perdidas por gênero: {e}")
            
            try:
                horas_perdidas_setor = analytics.horas_perdidas_por_setor(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
            except Exception as e:
                print(f"Erro ao calcular horas perdidas por setor: {e}")
            
            try:
                # Remove limite de meses para mostrar todos os meses disponíveis na planilha
                evolucao_mensal_horas = analytics.evolucao_mensal_horas(client_id, meses=0, mes_inicio=mes_inicio, mes_fim=mes_fim, funcionario=funcionario, setor=setor)
            except Exception as e:
                print(f"Erro ao calcular evolução mensal de horas: {e}")
            
            try:
                analise_detalhada_genero_data = analytics.analise_detalhada_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
            except Exception as e:
                print(f"Erro ao calcular análise detalhada por gênero: {e}")
            
            try:
                comparativo_dias_horas_genero_data = analytics.comparativo_dias_horas_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
            except Exception as e:
                print(f"Erro ao calcular comparativo dias/horas por gênero: {e}")
            
            try:
                horas_perdidas_setor_genero_data = analytics.horas_perdidas_setor_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
            except Exception as e:
                print(f"Erro ao calcular horas perdidas por setor e gênero: {e}")
        
        resultado = {
            "metricas": metricas,
            "top_cids": top_cids,
            "top_setores": top_setores,
            "evolucao_mensal": evolucao,
            "variacao_mensal": variacao_mensal,
            "distribuicao_genero": distribuicao_genero,
            "genero_mensal": genero_mensal,
            "top_funcionarios": top_funcionarios,
            "top_escalas": top_escalas,
            "top_motivos": top_motivos,
            "dias_centro_custo": dias_centro_custo,
            "distribuicao_dias": distribuicao_dias,
            "media_cid": media_cid,
            "evolucao_setor": evolucao_setor,
            "comparativo_dias_horas": comparativo_dias_horas,
            "frequencia_atestados": frequencia_atestados,
            "dias_setor_genero": dias_setor_genero,
            "produtividade": produtividade,
            "insights": insights,
            "alertas": alertas,
            "campos_mapeados": campos_disponiveis,  # Campos mapeados pelo cliente
            "campos_com_dados": campos_com_dados,  # Campos que realmente têm dados
            # Dados específicos para Roda de Ouro
            "classificacao_funcionarios_ro": classificacao_funcionarios_ro,
            "classificacao_setores_ro": classificacao_setores_ro,
            "classificacao_doencas_ro": classificacao_doencas_ro,
            "dias_ano_coerencia": dias_ano_coerencia,
            "analise_coerencia": analise_coerencia,
            "tempo_servico_atestados": tempo_servico_atestados,
            # Novas análises de horas e gênero (especialmente para Roda de Ouro)
            "horas_perdidas_genero": horas_perdidas_genero,
            "horas_perdidas_setor": horas_perdidas_setor,
            "evolucao_mensal_horas": evolucao_mensal_horas,
            "analise_detalhada_genero": analise_detalhada_genero_data,
            "comparativo_dias_horas_genero": comparativo_dias_horas_genero_data,
            "horas_perdidas_setor_genero": horas_perdidas_setor_genero_data,
            # Comparativo entre períodos
            "comparativo_periodos_mes": {},
            "comparativo_periodos_trimestre": {}
        }
        
        # Calcula comparativo entre períodos
        try:
            resultado["comparativo_periodos_mes"] = analytics.comparativo_periodos(client_id, tipo_comparacao='mes', funcionario=funcionario, setor=setor)
        except Exception as e:
            print(f"Erro ao calcular comparativo mensal: {e}")
        
        try:
            resultado["comparativo_periodos_trimestre"] = analytics.comparativo_periodos(client_id, tipo_comparacao='trimestre', funcionario=funcionario, setor=setor)
        except Exception as e:
            print(f"Erro ao calcular comparativo trimestral: {e}")
        
        # Corrige encoding antes de retornar
        return corrigir_encoding_json(resultado)
        
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao carregar dashboard: {error_detail}")

@app.get("/api/filtros")
async def obter_filtros(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retorna lista de funcionários e setores para preencher os filtros"""
    try:
        # Valida client_id
        validar_client_id(db, client_id)
        
        # Busca funcionários únicos
        funcionarios = db.query(Atestado.nomecompleto).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.nomecompleto != '',
            Atestado.nomecompleto.isnot(None)
        ).distinct().order_by(Atestado.nomecompleto).all()
        
        # Busca setores únicos
        setores = db.query(Atestado.setor).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.setor != '',
            Atestado.setor.isnot(None)
        ).distinct().order_by(Atestado.setor).all()
        
        return {
            "funcionarios": [f[0] for f in funcionarios if f[0]],
            "setores": [s[0] for s in setores if s[0]]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar filtros: {str(e)}")

# REMOVIDO: Endpoints de gráficos personalizados removidos
# Os gráficos agora são programados diretamente no código

# Endpoint removido para manter compatibilidade (retorna vazio)
@app.get("/api/clientes/{client_id}/graficos")
async def obter_graficos_configurados(
    client_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Endpoint removido - retorna vazio para compatibilidade"""
    return {
        "success": True,
        "client_id": client_id,
        "graficos": []
    }

@app.put("/api/clientes/{client_id}/graficos")
async def salvar_graficos_configurados(
    client_id: int, 
    request: Request, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Endpoint removido - não faz nada"""
    return {
        "success": True,
        "message": "Endpoint removido",
        "client_id": client_id,
        "graficos": []
    }

@app.post("/api/clientes/{client_id}/graficos/gerar-dados")
async def gerar_dados_grafico_personalizado(
    client_id: int, 
    request: Request, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Endpoint removido - retorna vazio para compatibilidade"""
    return {
        "success": True,
        "labels": [],
        "quantidades": [],
        "valores": [],
        "dados": [],
        "message": "Endpoint removido - gráficos agora são programados diretamente no código"
    }
    

@app.get("/api/clientes/{client_id}/campos-disponiveis")
async def obter_campos_disponiveis(
    client_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retorna os campos disponíveis para um cliente (mapeados e com dados)"""
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Busca mapeamento do cliente
        campos_mapeados = {}
        custom_fields = []
        try:
            mapping_obj = db.query(ClientColumnMapping).filter(ClientColumnMapping.client_id == client_id).first()
            if mapping_obj and mapping_obj.column_mapping:
                try:
                    mapping_data = json.loads(mapping_obj.column_mapping)
                    if isinstance(mapping_data, dict) and 'column_mapping' in mapping_data:
                        campos_mapeados = mapping_data.get('column_mapping', {})
                        custom_fields = mapping_data.get('custom_fields', [])
                    elif isinstance(mapping_data, dict):
                        campos_mapeados = mapping_data
                except:
                    pass
        except Exception as e:
            print(f"Erro ao buscar mapeamento: {e}")
        
        # Verifica quais campos têm dados reais no banco
        campos_com_dados = {}
        try:
            amostra = db.query(Atestado).join(Upload).filter(
                Upload.client_id == client_id
            ).limit(500).all()
            
            if amostra:
                campos_modelo = [
                    'nomecompleto', 'cpf', 'matricula', 'setor', 'centro_custo', 'cargo',
                    'genero', 'data_afastamento', 'data_retorno', 'cid', 'diagnostico',
                    'descricao_cid', 'dias_atestados', 'horas_perdi', 'motivo_atestado',
                    'escala', 'tipo_atestado', 'descricao_atestad', 'numero_dias_atestado',
                    'horas_perdidas', 'dias_perdidos'
                ]
                
                for campo in campos_modelo:
                    tem_dados = any(
                        getattr(reg, campo, None) not in (None, '', 0, 0.0) 
                        for reg in amostra
                    )
                    if tem_dados:
                        campos_com_dados[campo] = True
        except Exception as e:
            print(f"Erro ao verificar campos com dados: {e}")
        
        return {
            "success": True,
            "client_id": client_id,
            "campos_mapeados": campos_mapeados,  # Coluna da planilha -> Campo do sistema
            "campos_com_dados": list(campos_com_dados.keys()),  # Campos que têm dados
            "custom_fields": custom_fields  # Campos personalizados criados
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao obter campos disponíveis: {str(e)}")

@app.get("/api/alertas")
async def obter_alertas(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retorna alertas automáticos do sistema"""
    try:
        # Valida client_id
        validar_client_id(db, client_id)
        
        alertas_system = AlertasSystem(db)
        alertas = alertas_system.detectar_alertas(client_id, mes_inicio, mes_fim)
        return {
            "alertas": alertas,
            "total": len(alertas),
            "por_severidade": {
                "alta": len([a for a in alertas if a['severidade'] == 'alta']),
                "media": len([a for a in alertas if a['severidade'] == 'media']),
                "baixa": len([a for a in alertas if a['severidade'] == 'baixa'])
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar alertas: {str(e)}")

# ==================== MÓDULO CLIENTES ====================

class ClienteCreate(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    nome_fantasia: Optional[str] = None
    logo_url: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    inscricao_municipal: Optional[str] = None
    cep: Optional[str] = None
    endereco: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    situacao: Optional[str] = None
    data_abertura: Optional[str] = None
    atividade_principal: Optional[str] = None

@app.get("/api/clientes")
async def listar_clientes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista todos os clientes"""
    try:
        clientes = db.query(Client).order_by(Client.nome).all()
        return [
            {
                "id": c.id,
                "nome": c.nome,
                "cnpj": c.cnpj,
                "nome_fantasia": c.nome_fantasia,
                "cidade": c.cidade,
                "estado": c.estado,
                "telefone": c.telefone,
                "email": c.email,
                "situacao": c.situacao,
                "logo_url": c.logo_url,
                "cores_personalizadas": json.loads(c.cores_personalizadas) if c.cores_personalizadas else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "total_uploads": len(c.uploads)
            }
            for c in clientes
        ]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao listar clientes: {str(e)}")

@app.get("/api/clientes/{cliente_id}")
async def obter_cliente(
    cliente_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtém um cliente específico"""
    try:
        cliente = db.query(Client).filter(Client.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Busca logo principal da tabela client_logos
        logo_principal = db.query(ClientLogo).filter(
            ClientLogo.client_id == cliente_id,
            ClientLogo.is_principal == True
        ).first()
        
        # Usa logo principal se existir, senão usa o logo_url do cliente (compatibilidade)
        logo_url_final = logo_principal.logo_url if logo_principal else cliente.logo_url
        
        return {
            "id": cliente.id,
            "nome": cliente.nome,
            "cnpj": cliente.cnpj,
            "nome_fantasia": cliente.nome_fantasia,
            "inscricao_estadual": cliente.inscricao_estadual,
            "inscricao_municipal": cliente.inscricao_municipal,
            "cep": cliente.cep,
            "endereco": cliente.endereco,
            "numero": cliente.numero,
            "complemento": cliente.complemento,
            "bairro": cliente.bairro,
            "cidade": cliente.cidade,
            "estado": cliente.estado,
            "telefone": cliente.telefone,
            "email": cliente.email,
            "situacao": cliente.situacao,
            "logo_url": logo_url_final,
            "cores_personalizadas": json.loads(cliente.cores_personalizadas) if cliente.cores_personalizadas else None,
            "data_abertura": cliente.data_abertura.isoformat() if cliente.data_abertura else None,
            "atividade_principal": cliente.atividade_principal,
            "created_at": cliente.created_at.isoformat() if cliente.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao obter cliente: {str(e)}")

@app.post("/api/clientes/{cliente_id}/clonar_dados")
async def clonar_dados_cliente(
    cliente_id: int,
    origem_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Replica dados (uploads + atestados) de um cliente origem para o cliente destino."""
    try:
        if cliente_id == origem_id:
            raise HTTPException(status_code=400, detail="Cliente destino e origem não podem ser o mesmo.")

        destino = db.query(Client).filter(Client.id == cliente_id).first()
        if not destino:
            raise HTTPException(status_code=404, detail="Cliente destino não encontrado.")

        origem = db.query(Client).filter(Client.id == origem_id).first()
        if not origem:
            raise HTTPException(status_code=404, detail="Cliente origem não encontrado.")

        if len(destino.uploads) > 0:
            raise HTTPException(status_code=400, detail="Cliente destino já possui dados cadastrados.")

        uploads_origem = db.query(Upload).filter(Upload.client_id == origem_id).all()
        if not uploads_origem:
            raise HTTPException(status_code=400, detail="Cliente origem não possui dados para replicar.")

        total_uploads = 0
        total_atestados = 0

        for upload in uploads_origem:
            novo_nome_arquivo = upload.filename
            if upload.filename:
                caminho_origem = os.path.join(UPLOADS_DIR, upload.filename)
                if os.path.exists(caminho_origem):
                    base, ext = os.path.splitext(upload.filename)
                    novo_nome_arquivo = f"clone_{destino.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}{ext}"
                    os.makedirs(UPLOADS_DIR, exist_ok=True)
                    try:
                        shutil.copy2(caminho_origem, os.path.join(UPLOADS_DIR, novo_nome_arquivo))
                    except Exception as copia_erro:
                        print(f"Não foi possível copiar arquivo {upload.filename}: {copia_erro}")
                        novo_nome_arquivo = upload.filename

            novo_upload = Upload(
                client_id=destino.id,
                filename=novo_nome_arquivo,
                mes_referencia=upload.mes_referencia,
                data_upload=datetime.now(),
                total_registros=upload.total_registros
            )
            db.add(novo_upload)
            db.flush()
            total_uploads += 1

            for atestado in upload.atestados:
                novo_atestado = Atestado(
                    upload_id=novo_upload.id,
                    nomecompleto=atestado.nomecompleto,
                    descricao_atestad=atestado.descricao_atestad,
                    dias_atestados=atestado.dias_atestados,
                    cid=atestado.cid,
                    diagnostico=atestado.diagnostico,
                    centro_custo=atestado.centro_custo,
                    setor=atestado.setor,
                    motivo_atestado=atestado.motivo_atestado,
                    escala=atestado.escala,
                    horas_dia=atestado.horas_dia,
                    horas_perdi=atestado.horas_perdi,
                    nome_funcionario=atestado.nome_funcionario,
                    cpf=atestado.cpf,
                    matricula=atestado.matricula,
                    cargo=atestado.cargo,
                    genero=atestado.genero,
                    data_afastamento=atestado.data_afastamento,
                    data_retorno=atestado.data_retorno,
                    tipo_info_atestado=atestado.tipo_info_atestado,
                    tipo_atestado=atestado.tipo_atestado,
                    descricao_cid=atestado.descricao_cid,
                    numero_dias_atestado=atestado.numero_dias_atestado,
                    numero_horas_atestado=atestado.numero_horas_atestado,
                    dias_perdidos=atestado.dias_perdidos,
                    horas_perdidas=atestado.horas_perdidas,
                    dados_originais=atestado.dados_originais
                )
                db.add(novo_atestado)
                total_atestados += 1

        destino.updated_at = datetime.now()
        db.commit()
        db.refresh(destino)

        return {
            "message": "Dados replicados com sucesso.",
            "total_uploads": len(destino.uploads),
            "total_atestados": total_atestados
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao clonar dados: {str(e)}")

@app.post("/api/clientes")
async def criar_cliente(
    cliente: ClienteCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Cria um novo cliente"""
    try:
        # Verifica se CNPJ já existe
        if cliente.cnpj:
            cnpj_limpo = re.sub(r'\D', '', cliente.cnpj)
            cliente_existente = db.query(Client).filter(Client.cnpj == cnpj_limpo).first()
            if cliente_existente:
                raise HTTPException(status_code=400, detail="CNPJ já cadastrado")
        
        # Converte data_abertura se fornecida
        data_abertura = None
        if cliente.data_abertura:
            try:
                data_abertura = datetime.strptime(cliente.data_abertura, '%Y-%m-%d').date()
            except:
                pass
        
        logo_url = None
        if cliente.logo_url:
            logo_url = cliente.logo_url.strip() or None

        novo_cliente = Client(
            nome=cliente.nome,
            cnpj=re.sub(r'\D', '', cliente.cnpj) if cliente.cnpj else None,
            nome_fantasia=cliente.nome_fantasia,
            logo_url=logo_url,
            inscricao_estadual=cliente.inscricao_estadual,
            inscricao_municipal=cliente.inscricao_municipal,
            cep=cliente.cep,
            endereco=cliente.endereco,
            numero=cliente.numero,
            complemento=cliente.complemento,
            bairro=cliente.bairro,
            cidade=cliente.cidade,
            estado=cliente.estado,
            telefone=cliente.telefone,
            email=cliente.email,
            situacao=cliente.situacao,
            data_abertura=data_abertura,
            atividade_principal=cliente.atividade_principal
        )
        
        db.add(novo_cliente)
        db.commit()
        db.refresh(novo_cliente)
        
        return {
            "id": novo_cliente.id,
            "nome": novo_cliente.nome,
            "cnpj": novo_cliente.cnpj,
            "message": "Cliente criado com sucesso"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao criar cliente: {str(e)}")

@app.put("/api/clientes/{cliente_id}")
async def atualizar_cliente(
    cliente_id: int, 
    cliente: ClienteCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualiza um cliente"""
    try:
        cliente_db = db.query(Client).filter(Client.id == cliente_id).first()
        if not cliente_db:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Verifica se CNPJ já existe em outro cliente
        if cliente.cnpj:
            cnpj_limpo = re.sub(r'\D', '', cliente.cnpj)
            cliente_existente = db.query(Client).filter(
                Client.cnpj == cnpj_limpo,
                Client.id != cliente_id
            ).first()
            if cliente_existente:
                raise HTTPException(status_code=400, detail="CNPJ já cadastrado em outro cliente")
        
        # NÃO atualiza logo_url aqui quando vem null, pois agora usamos múltiplos logos via tabela client_logos
        # O logo_url do cliente é atualizado automaticamente quando um logo é marcado como principal
        # Apenas remove o logo se explicitamente enviado como string vazia
        logo_url_novo = cliente.logo_url
        if logo_url_novo is not None:
            logo_url_novo = logo_url_novo.strip() if isinstance(logo_url_novo, str) else None
            if logo_url_novo == '':
                # Se enviado como string vazia, não remove (mantém o atual)
                # Os logos são gerenciados via tabela client_logos
                pass
            # Se null, também não faz nada (mantém o atual)

        cliente_db.nome = cliente.nome
        cliente_db.cnpj = re.sub(r'\D', '', cliente.cnpj) if cliente.cnpj else None
        cliente_db.nome_fantasia = cliente.nome_fantasia
        cliente_db.inscricao_estadual = cliente.inscricao_estadual
        cliente_db.inscricao_municipal = cliente.inscricao_municipal
        cliente_db.cep = cliente.cep
        cliente_db.endereco = cliente.endereco
        cliente_db.numero = cliente.numero
        cliente_db.complemento = cliente.complemento
        cliente_db.bairro = cliente.bairro
        cliente_db.cidade = cliente.cidade
        cliente_db.estado = cliente.estado
        cliente_db.telefone = cliente.telefone
        cliente_db.email = cliente.email
        cliente_db.situacao = cliente.situacao
        if cliente.data_abertura:
            try:
                cliente_db.data_abertura = datetime.strptime(cliente.data_abertura, '%Y-%m-%d').date()
            except:
                pass
        cliente_db.atividade_principal = cliente.atividade_principal
        cliente_db.updated_at = datetime.now()
        
        db.commit()
        db.refresh(cliente_db)
        
        return {
            "id": cliente_db.id,
            "nome": cliente_db.nome,
            "message": "Cliente atualizado com sucesso"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar cliente: {str(e)}")

@app.post("/api/clientes/{cliente_id}/logo")
async def upload_logo_cliente(
    cliente_id: int,
    arquivo: UploadFile = File(...),
    descricao: Optional[str] = Form(None),
    is_principal: Optional[str] = Form("false"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Adiciona um novo logo para um cliente (suporte a múltiplos logos)."""
    try:
        cliente = db.query(Client).filter(Client.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        if not arquivo:
            raise HTTPException(status_code=400, detail="Arquivo de logo não enviado")

        conteudo = await arquivo.read()
        if not conteudo:
            raise HTTPException(status_code=400, detail="Arquivo inválido")

        tamanho_max = 1 * 1024 * 1024  # 1 MB
        if len(conteudo) > tamanho_max:
            raise HTTPException(status_code=400, detail="Logo deve ter no máximo 1 MB")

        extensao = os.path.splitext(arquivo.filename or '')[1].lower()
        if not extensao:
            tipo = (arquivo.content_type or '').lower()
            mapa_extensoes = {
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/webp": ".webp",
                "image/svg+xml": ".svg"
            }
            extensao = mapa_extensoes.get(tipo, '')

        extensoes_permitidas = {".png", ".jpg", ".jpeg", ".svg", ".webp"}
        if extensao not in extensoes_permitidas:
            raise HTTPException(status_code=400, detail="Formato de logo não suportado (use PNG, JPG, SVG ou WEBP)")

        os.makedirs(LOGOS_DIR, exist_ok=True)
        nome_arquivo = f"cliente_{cliente_id}_{uuid.uuid4().hex}{extensao}"
        caminho_destino = os.path.join(LOGOS_DIR, nome_arquivo)

        with open(caminho_destino, "wb") as destino:
            destino.write(conteudo)

        novo_logo_url = f"/static/logos/{nome_arquivo}"

        # Converte is_principal de string para boolean
        is_principal_bool = str(is_principal).lower() in ('true', '1', 'yes', 'on')

        # IMPORTANTE: NÃO remove logos antigos, apenas adiciona um novo
        # Se este logo for marcado como principal, remove a marcação dos outros (mas mantém os logos)
        if is_principal_bool:
            db.query(ClientLogo).filter(
                ClientLogo.client_id == cliente_id,
                ClientLogo.is_principal == True
            ).update({"is_principal": False})

        # Cria novo registro de logo (NÃO substitui, ADICIONA)
        novo_logo = ClientLogo(
            client_id=cliente_id,
            logo_url=novo_logo_url,
            is_principal=is_principal_bool,
            descricao=descricao
        )
        db.add(novo_logo)

        # Se não há logo principal definido, define este como principal
        if not is_principal_bool:
            logo_principal_existente = db.query(ClientLogo).filter(
                ClientLogo.client_id == cliente_id,
                ClientLogo.is_principal == True
            ).first()
            if not logo_principal_existente:
                novo_logo.is_principal = True

        # Atualiza logo_url do cliente para o logo principal (compatibilidade)
        logo_principal = db.query(ClientLogo).filter(
            ClientLogo.client_id == cliente_id,
            ClientLogo.is_principal == True
        ).first()
        if logo_principal:
            cliente.logo_url = logo_principal.logo_url

        cliente.updated_at = datetime.now()
        db.commit()
        db.refresh(novo_logo)

        return {
            "id": novo_logo.id,
            "logo_url": novo_logo.logo_url,
            "is_principal": novo_logo.is_principal,
            "descricao": novo_logo.descricao,
            "message": "Logo adicionado com sucesso"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao enviar logo: {str(e)}")

@app.get("/api/clientes/{cliente_id}/logos")
async def listar_logos_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista todos os logos de um cliente."""
    try:
        logos = db.query(ClientLogo).filter(ClientLogo.client_id == cliente_id).order_by(
            ClientLogo.is_principal.desc(),
            ClientLogo.created_at.desc()
        ).all()
        
        return {
            "logos": [
                {
                    "id": logo.id,
                    "logo_url": logo.logo_url,
                    "is_principal": logo.is_principal,
                    "descricao": logo.descricao,
                    "created_at": logo.created_at.isoformat() if logo.created_at else None
                }
                for logo in logos
            ]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao listar logos: {str(e)}")

@app.put("/api/clientes/{cliente_id}/logos/{logo_id}/principal")
async def definir_logo_principal(
    cliente_id: int,
    logo_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Define um logo como principal."""
    try:
        logo = db.query(ClientLogo).filter(
            ClientLogo.id == logo_id,
            ClientLogo.client_id == cliente_id
        ).first()
        
        if not logo:
            raise HTTPException(status_code=404, detail="Logo não encontrado")
        
        # Remove marcação de principal dos outros logos
        db.query(ClientLogo).filter(
            ClientLogo.client_id == cliente_id,
            ClientLogo.is_principal == True,
            ClientLogo.id != logo_id
        ).update({"is_principal": False})
        
        # Define este como principal
        logo.is_principal = True
        
        # Atualiza logo_url do cliente (compatibilidade)
        cliente = db.query(Client).filter(Client.id == cliente_id).first()
        if cliente:
            cliente.logo_url = logo.logo_url
            cliente.updated_at = datetime.now()
        
        db.commit()
        db.refresh(logo)
        
        return {
            "id": logo.id,
            "logo_url": logo.logo_url,
            "is_principal": logo.is_principal,
            "message": "Logo definido como principal"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao definir logo principal: {str(e)}")

@app.delete("/api/clientes/{cliente_id}/logos/{logo_id}")
async def deletar_logo_cliente(
    cliente_id: int,
    logo_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Deleta um logo de um cliente."""
    try:
        logo = db.query(ClientLogo).filter(
            ClientLogo.id == logo_id,
            ClientLogo.client_id == cliente_id
        ).first()
        
        if not logo:
            raise HTTPException(status_code=404, detail="Logo não encontrado")
        
        # Remove arquivo físico
        if logo.logo_url:
            remover_logo_arquivo(logo.logo_url)
        
        # Se era o principal, define outro como principal (se houver)
        if logo.is_principal:
            outro_logo = db.query(ClientLogo).filter(
                ClientLogo.client_id == cliente_id,
                ClientLogo.id != logo_id
            ).first()
            
            if outro_logo:
                outro_logo.is_principal = True
                cliente = db.query(Client).filter(Client.id == cliente_id).first()
                if cliente:
                    cliente.logo_url = outro_logo.logo_url
            else:
                cliente = db.query(Client).filter(Client.id == cliente_id).first()
                if cliente:
                    cliente.logo_url = None
        
        db.delete(logo)
        db.commit()
        
        return {"message": "Logo deletado com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar logo: {str(e)}")

@app.delete("/api/clientes/{cliente_id}")
async def deletar_cliente(
    cliente_id: int, 
    forcar: bool = Query(False, description="Forçar exclusão mesmo com dados"),
    db: Session = Depends(get_db)
):
    """Deleta um cliente. Se forcar=True, deleta também todos os dados relacionados."""
    try:
        cliente = db.query(Client).filter(Client.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Verifica se tem uploads
        tem_uploads = len(cliente.uploads) > 0
        
        if tem_uploads and not forcar:
            raise HTTPException(status_code=400, detail="Cliente possui dados. Utilize o arquivo morto ou force a exclusão com forcar=true.")
        
        # Se forçar exclusão, deleta todos os dados relacionados primeiro
        if forcar and tem_uploads:
            # Deleta todos os atestados relacionados aos uploads
            from .models import Atestado
            for upload in cliente.uploads:
                db.query(Atestado).filter(Atestado.upload_id == upload.id).delete()
            
            # Deleta todos os uploads
            db.query(Upload).filter(Upload.client_id == cliente_id).delete()
            
            # Deleta todos os logos
            from .models import ClientLogo
            db.query(ClientLogo).filter(ClientLogo.client_id == cliente_id).delete()
            
            # Deleta mapeamentos de colunas
            from .models import ClientColumnMapping
            db.query(ClientColumnMapping).filter(ClientColumnMapping.client_id == cliente_id).delete()
        
        # Deleta o cliente
        db.delete(cliente)
        db.commit()
        
        return {"message": "Cliente deletado com sucesso" + (" (incluindo todos os dados)" if forcar else "")}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar cliente: {str(e)}")

@app.post("/api/clientes/{cliente_id}/arquivar")
async def arquivar_cliente(
    cliente_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Move um cliente para o arquivo morto (mantém dados)"""
    try:
        cliente = db.query(Client).filter(Client.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        if len(cliente.uploads) == 0:
            raise HTTPException(status_code=400, detail="Cliente não possui dados para arquivar. Utilize a exclusão.")

        cliente.situacao = "ARQUIVO MORTO"
        cliente.updated_at = datetime.now()
        db.commit()
        db.refresh(cliente)

        return {
            "message": "Cliente movido para arquivo morto.",
            "cliente": {
                "id": cliente.id,
                "situacao": cliente.situacao,
                "updated_at": cliente.updated_at.isoformat() if cliente.updated_at else None,
                "total_uploads": len(cliente.uploads)
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao mover para arquivo morto: {str(e)}")

@app.put("/api/clientes/{cliente_id}/cores")
async def salvar_cores_cliente(
    cliente_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Salva as cores personalizadas de um cliente"""
    try:
        cliente = db.query(Client).filter(Client.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        body = await request.json()
        cores = body.get('cores', {})
        
        # Valida estrutura básica
        if not isinstance(cores, dict):
            raise HTTPException(status_code=400, detail="Cores devem ser um objeto JSON")
        
        # Salva como JSON string
        cliente.cores_personalizadas = json.dumps(cores)
        cliente.updated_at = datetime.now()
        
        db.commit()
        db.refresh(cliente)
        
        return {
            "success": True,
            "message": "Cores salvas com sucesso",
            "cores": json.loads(cliente.cores_personalizadas) if cliente.cores_personalizadas else None
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar cores: {str(e)}")

@app.get("/api/clientes/{cliente_id}/cores")
async def obter_cores_cliente(
    cliente_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtém as cores personalizadas de um cliente"""
    try:
        cliente = db.query(Client).filter(Client.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        cores = None
        if cliente.cores_personalizadas:
            try:
                cores = json.loads(cliente.cores_personalizadas)
            except:
                cores = None
        
        return {
            "success": True,
            "cores": cores
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao obter cores: {str(e)}")

@app.post("/api/clientes/{cliente_id}/ativar")
async def ativar_cliente(
    cliente_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Reativa um cliente anteriormente arquivado"""
    try:
        cliente = db.query(Client).filter(Client.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        cliente.situacao = "ATIVO"
        cliente.updated_at = datetime.now()
        db.commit()
        db.refresh(cliente)

        return {
            "message": "Cliente reativado com sucesso.",
            "cliente": {
                "id": cliente.id,
                "situacao": cliente.situacao,
                "updated_at": cliente.updated_at.isoformat() if cliente.updated_at else None,
                "total_uploads": len(cliente.uploads)
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao reativar cliente: {str(e)}")

# ==================== API - MAPEAMENTO DE COLUNAS ====================

@app.get("/api/clientes/{client_id}/column-mapping")
async def get_column_mapping(
    client_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtém o mapeamento de colunas de um cliente"""
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        mapping = db.query(ClientColumnMapping).filter(ClientColumnMapping.client_id == client_id).first()
        
        if mapping:
            try:
                mapping_data = json.loads(mapping.column_mapping)
                # Suporta formato antigo (só column_mapping) e novo (com custom_fields)
                if isinstance(mapping_data, dict) and 'column_mapping' in mapping_data:
                    return {
                        "client_id": client_id,
                        "column_mapping": mapping_data.get('column_mapping', {}),
                        "custom_fields": mapping_data.get('custom_fields', []),
                        "created_at": mapping.created_at.isoformat() if mapping.created_at else None,
                        "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None
                    }
                else:
                    # Formato antigo - só column_mapping
                    return {
                        "client_id": client_id,
                        "column_mapping": mapping_data if isinstance(mapping_data, dict) else {},
                        "custom_fields": [],
                        "created_at": mapping.created_at.isoformat() if mapping.created_at else None,
                        "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None
                    }
            except:
                return {
                    "client_id": client_id,
                    "column_mapping": {},
                    "custom_fields": [],
                    "message": "Erro ao ler mapeamento"
                }
        else:
            return {
                "client_id": client_id,
                "column_mapping": {},
                "custom_fields": [],
                "message": "Nenhum mapeamento configurado"
            }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao obter mapeamento: {str(e)}")

@app.put("/api/clientes/{client_id}/column-mapping")
async def save_column_mapping(
    client_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Salva o mapeamento de colunas de um cliente"""
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        body = await request.json()
        column_mapping = body.get('column_mapping', {})
        custom_fields = body.get('custom_fields', [])
        
        # Valida o mapeamento (deve ser um dicionário)
        if not isinstance(column_mapping, dict):
            raise HTTPException(status_code=400, detail="Mapeamento deve ser um objeto JSON")
        
        # Valida campos personalizados
        if not isinstance(custom_fields, list):
            raise HTTPException(status_code=400, detail="Campos personalizados devem ser uma lista")
        
        # Campos válidos do sistema (incluindo campos personalizados)
        campos_validos = [
            'nomecompleto', 'nome_funcionario', 'cpf', 'matricula', 'cargo',
            'setor', 'centro_custo', 'genero', 'data_afastamento', 'data_retorno',
            'cid', 'diagnostico', 'descricao_cid', 'descricao_atestad',
            'dias_atestados', 'numero_dias_atestado', 'dias_perdidos',
            'horas_dia', 'horas_perdi', 'horas_perdidas', 'numero_horas_atestado',
            'motivo_atestado', 'escala', 'tipo_atestado', 'tipo_info_atestado'
        ]
        
        # Adiciona campos personalizados à lista de válidos
        for campo_personalizado in custom_fields:
            if isinstance(campo_personalizado, dict) and 'value' in campo_personalizado:
                campos_validos.append(campo_personalizado['value'].lower())
        
        # Valida se os campos mapeados são válidos (agora permite campos personalizados)
        for col_planilha, campo_sistema in column_mapping.items():
            if campo_sistema.lower() not in campos_validos:
                # Permite campos personalizados mesmo que não estejam na lista padrão
                campo_personalizado_existe = any(
                    cf.get('value', '').lower() == campo_sistema.lower() 
                    for cf in custom_fields if isinstance(cf, dict)
                )
                if not campo_personalizado_existe:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Campo '{campo_sistema}' não é válido. Use um campo do sistema ou crie um campo personalizado."
                    )
        
        # Busca ou cria mapeamento
        mapping = db.query(ClientColumnMapping).filter(ClientColumnMapping.client_id == client_id).first()
        
        # Salva campos personalizados no campo column_mapping como JSON adicional
        # ou em um campo separado se existir
        mapping_data = {
            'column_mapping': column_mapping,
            'custom_fields': custom_fields
        }
        
        if mapping:
            mapping.column_mapping = json.dumps(mapping_data, ensure_ascii=False)
            mapping.updated_at = datetime.now()
        else:
            mapping = ClientColumnMapping(
                client_id=client_id,
                column_mapping=json.dumps(mapping_data, ensure_ascii=False)
            )
            db.add(mapping)
        
        db.commit()
        db.refresh(mapping)
        
        return {
            "message": "Mapeamento salvo com sucesso",
            "client_id": client_id,
            "column_mapping": column_mapping,
            "custom_fields": custom_fields,
            "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar mapeamento: {str(e)}")

@app.post("/api/clientes/{client_id}/column-mapping/preview")
async def preview_column_mapping(
    client_id: int,
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Preview do mapeamento de colunas usando uma planilha de exemplo"""
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        if not file.filename or not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Arquivo inválido. Use .xlsx ou .xls")
        
        # Salva arquivo temporário
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        try:
            # Lê planilha
            df = pd.read_excel(tmp_path, sheet_name=0, engine='openpyxl', nrows=5)  # Apenas 5 linhas para preview
            
            # Parse do mapeamento
            mapping_dict = {}
            if column_mapping:
                try:
                    mapping_dict = json.loads(column_mapping)
                except:
                    pass
            
            # Aplica mapeamento
            processor = ExcelProcessor(tmp_path, custom_mapping=mapping_dict if mapping_dict else None)
            if processor.ler_planilha():
                processor.padronizar_colunas()
                
                # Retorna preview
                preview_data = []
                for idx, row in processor.df.head(3).iterrows():
                    preview_data.append(row.to_dict())
                
                return {
                    "success": True,
                    "columns_original": list(df.columns),
                    "columns_mapped": list(processor.df.columns),
                    "preview": preview_data,
                    "total_rows": len(processor.df)
                }
            else:
                raise HTTPException(status_code=400, detail="Erro ao ler planilha")
        finally:
            # Remove arquivo temporário
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao fazer preview: {str(e)}")

@app.get("/api/buscar-cnpj/{cnpj}")
async def buscar_cnpj(cnpj: str):
    """Busca dados da empresa por CNPJ usando ReceitaWS"""
    try:
        # Remove caracteres não numéricos
        cnpj_limpo = re.sub(r'\D', '', cnpj)
        
        if len(cnpj_limpo) != 14:
            raise HTTPException(status_code=400, detail="CNPJ deve ter 14 dígitos")
        
        # API ReceitaWS (gratuita, sem autenticação)
        url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj_limpo}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Verifica se a API retornou erro
            if 'status' in data and data['status'] == 'ERROR':
                raise HTTPException(status_code=404, detail=data.get('message', 'CNPJ não encontrado'))
            
            # Formata os dados retornados
            resultado = {
                "nome": data.get('nome', ''),
                "cnpj": data.get('cnpj', ''),
                "nome_fantasia": data.get('fantasia', ''),
                "inscricao_estadual": data.get('inscricao_estadual', ''),
                "inscricao_municipal": data.get('inscricao_municipal', ''),
                "cep": data.get('cep', '').replace('-', '') if data.get('cep') else '',
                "endereco": data.get('logradouro', ''),
                "numero": data.get('numero', ''),
                "complemento": data.get('complemento', ''),
                "bairro": data.get('bairro', ''),
                "cidade": data.get('municipio', ''),
                "estado": data.get('uf', ''),
                "telefone": data.get('telefone', ''),
                "email": data.get('email', ''),
                "situacao": data.get('situacao', ''),
                "data_abertura": data.get('abertura', ''),
                "atividade_principal": data.get('atividade_principal', [{}])[0].get('text', '') if data.get('atividade_principal') else ''
            }
            
            return resultado
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=503, detail=f"Erro ao consultar ReceitaWS: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao processar dados do CNPJ: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar CNPJ: {str(e)}")

@app.get("/clientes")
async def pagina_clientes():
    """Página de gerenciamento de clientes"""
    return FileResponse("frontend/clientes.html")

@app.get("/apresentacao")
async def pagina_apresentacao():
    """Página de apresentação de gráficos"""
    return FileResponse("frontend/apresentacao.html")

@app.get("/api/apresentacao")
async def dados_apresentacao(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    funcionario: Optional[List[str]] = Query(None),
    setor: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retorna todos os dados necessários para a apresentação com análises IA"""
    try:
        print(f"[APRESENTACAO] ===== INÍCIO - Recebido client_id: {client_id} (tipo: {type(client_id)}) =====")
        import time
        inicio = time.time()
        
        # Valida client_id
        client = validar_client_id(db, client_id)
        print(f"[APRESENTACAO] Cliente validado: {client.nome}")
        
        analytics = Analytics(db)
        insights_engine = InsightsEngine(db)
        
        # Busca todas as métricas e dados (igual ao dashboard)
        try:
            metricas = analytics.metricas_gerais(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular métricas gerais: {e}")
            metricas = {
                "total_atestados_dias": 0,
                "total_dias_perdidos": 0,
                "total_horas_perdidas": 0
            }
        
        try:
            top_cids = analytics.top_cids(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular top CIDs: {e}")
            top_cids = []
        
        try:
            top_setores = analytics.top_setores(client_id, 5, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular top setores: {e}")
            top_setores = []
        
        try:
            evolucao = analytics.evolucao_mensal(client_id, 12, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular evolução mensal: {e}")
            evolucao = []
        
        # Calcula variações mês a mês
        variacao_mensal = []
        if evolucao:
            anterior = None
            for item in evolucao:
                current_dias = float(item.get('dias_perdidos') or 0)
                current_horas = float(item.get('horas_perdidas') or 0)
                registro = {
                    "mes": item.get('mes'),
                    "dias": round(current_dias, 2),
                    "horas": round(current_horas, 2),
                    "variacao_dias": 0.0,
                    "variacao_horas": 0.0,
                    "percentual_dias": None,
                    "percentual_horas": None
                }
                
                if anterior:
                    variacao_dias = current_dias - anterior.get('dias_perdidos', 0)
                    variacao_horas = current_horas - anterior.get('horas_perdidas', 0)
                    registro["variacao_dias"] = round(variacao_dias, 2)
                    registro["variacao_horas"] = round(variacao_horas, 2)
                    registro["percentual_dias"] = round(((variacao_dias / anterior.get('dias_perdidos', 1)) * 100), 2) if anterior.get('dias_perdidos') else None
                    registro["percentual_horas"] = round(((variacao_horas / anterior.get('horas_perdidas', 1)) * 100), 2) if anterior.get('horas_perdidas') else None
                
                variacao_mensal.append(registro)
                anterior = {
                    'dias_perdidos': current_dias,
                    'horas_perdidas': current_horas
                }
        
        try:
            distribuicao_genero = analytics.distribuicao_genero_funcionarios(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular distribuição de gênero: {e}")
            distribuicao_genero = []
        
        try:
            genero_mensal = analytics.distribuicao_genero_mensal(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular distribuição mensal por gênero: {e}")
            genero_mensal = []
        
        try:
            top_funcionarios = analytics.top_funcionarios(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular top funcionários: {e}")
            top_funcionarios = []
        
        try:
            top_escalas = analytics.top_escalas(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular top escalas: {e}")
            top_escalas = []
        
        try:
            top_motivos = analytics.top_motivos(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular top motivos: {e}")
            top_motivos = []
        
        try:
            dias_centro_custo = analytics.dias_perdidos_por_centro_custo(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular dias por centro de custo: {e}")
            dias_centro_custo = []
        
        try:
            distribuicao_dias = analytics.distribuicao_dias_por_atestado(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular distribuição de dias: {e}")
            distribuicao_dias = []
        
        try:
            media_cid = analytics.media_dias_por_cid(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular média por CID: {e}")
            media_cid = []
        
        try:
            top_cids_dias = analytics.top_cids(client_id, 5, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular top CIDs para dias: {e}")
            top_cids_dias = []
        
        try:
            dias_setor_genero = analytics.dias_perdidos_setor_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular dias por setor e gênero: {e}")
            dias_setor_genero = []
        
        # Gera análises IA para cada gráfico - ISOLADO POR EMPRESA
        slides = []
        
        # Slide 0: Título/Capa (sempre presente)
        slides.append({
            "id": 0,
            "tipo": "capa",
            "titulo": "Capa",
            "subtitulo": "",
            "dados": None,
            "analise": None
        })
        
        # ==================== CONVERPLAST (client_id = 2) ====================
        if client_id == 2:
            # Slide 1: KPIs
            if metricas:
                try:
                    analise_kpis = insights_engine.gerar_analise_grafico('kpis', None, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise KPIs: {e}")
                    analise_kpis = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "kpis",
                    "titulo": "Indicadores Principais",
                    "subtitulo": "Visão geral do absenteísmo",
                    "dados": metricas,
                    "analise": analise_kpis
                })
            
            # Slide 2: Dias Perdidos por Funcionário
            if top_funcionarios:
                try:
                    analise_func = insights_engine.gerar_analise_grafico('funcionarios_dias', top_funcionarios, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise funcionários: {e}")
                    analise_func = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "funcionarios_dias",
                    "titulo": "Dias Perdidos por Funcionário",
                    "subtitulo": "TOP 10 funcionários com maior índice",
                    "dados": top_funcionarios,
                    "analise": analise_func
                })
            
            # Slide 3: TOP 10 CIDs
            if top_cids:
                try:
                    analise_cids = insights_engine.gerar_analise_grafico('top_cids', top_cids, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise CIDs: {e}")
                    analise_cids = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "top_cids",
                    "titulo": "TOP 10 Doenças mais Frequentes",
                    "subtitulo": "Principais causas de afastamento",
                    "dados": top_cids,
                    "analise": analise_cids
                })
            
            # Slide 4: Evolução Mensal
            if evolucao:
                try:
                    analise_evol = insights_engine.gerar_analise_grafico('evolucao_mensal', evolucao, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise evolução: {e}")
                    analise_evol = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "evolucao_mensal",
                    "titulo": "Evolução Mensal",
                    "subtitulo": "Últimos 12 meses",
                    "dados": evolucao,
                    "analise": analise_evol
                })
            
            # Slide 4.1: Quantidade de Atestados por Mês
            if evolucao:
                slides.append({
                    "id": len(slides),
                    "tipo": "quantidade_atestados",
                    "titulo": "Quantidade de Atestados por Mês",
                    "subtitulo": "Total de atestados registrados mensalmente",
                    "dados": evolucao,
                    "analise": "Acompanhamento da quantidade total de atestados ao longo dos meses."
                })
            
            # Slide 4.2: Variação Mensal
            if variacao_mensal:
                slides.append({
                    "id": len(slides),
                    "tipo": "variacao_mensal",
                    "titulo": "Variação Mensal",
                    "subtitulo": "Diferença mês a mês (dias x horas)",
                    "dados": variacao_mensal,
                    "analise": "Análise das variações mensais para identificar tendências de aumento ou redução."
                })
            
            # Slide 4.3: Distribuição Mensal por Gênero
            if genero_mensal:
                slides.append({
                    "id": len(slides),
                    "tipo": "genero_mensal",
                    "titulo": "Distribuição Mensal por Gênero",
                    "subtitulo": "Participação mensal de Masculino x Feminino",
                    "dados": genero_mensal,
                    "analise": "Acompanhamento da distribuição por gênero ao longo dos meses."
                })
            
            # Slide 5: TOP 5 Setores
            if top_setores:
                try:
                    analise_setores = insights_engine.gerar_analise_grafico('top_setores', top_setores, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise setores: {e}")
                    analise_setores = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "top_setores",
                    "titulo": "TOP 5 Setores",
                    "subtitulo": "Setores com mais atestados",
                    "dados": top_setores,
                    "analise": analise_setores
                })
            
            # Slide 6: Por Gênero
            if distribuicao_genero:
                try:
                    analise_genero = insights_engine.gerar_analise_grafico('genero', distribuicao_genero, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise gênero: {e}")
                    analise_genero = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "genero",
                    "titulo": "Distribuição por Gênero",
                    "subtitulo": "Masculino vs Feminino",
                    "dados": distribuicao_genero,
                    "analise": analise_genero
                })
            
            # Slide 7: Dias por Doença
            if top_cids_dias:
                try:
                    analise_doenca = insights_engine.gerar_analise_grafico('dias_doenca', top_cids_dias, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise doença: {e}")
                    analise_doenca = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "dias_doenca",
                    "titulo": "Dias por Doença",
                    "subtitulo": "Total de dias perdidos",
                    "dados": top_cids_dias,
                    "analise": analise_doenca
                })
            
            # Slide 8: Escalas
            if top_escalas:
                try:
                    analise_escalas = insights_engine.gerar_analise_grafico('escalas', top_escalas, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise escalas: {e}")
                    analise_escalas = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "escalas",
                    "titulo": "Escalas com mais Atestados",
                    "subtitulo": "TOP 10 escalas com maior incidência",
                    "dados": top_escalas,
                    "analise": analise_escalas
                })
            
            # Slide 9: Motivos
            if top_motivos:
                try:
                    analise_motivos = insights_engine.gerar_analise_grafico('motivos', top_motivos, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise motivos: {e}")
                    analise_motivos = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "motivos",
                    "titulo": "Motivos de Incidência",
                    "subtitulo": "Distribuição percentual dos motivos",
                    "dados": top_motivos,
                    "analise": analise_motivos
                })
            
            # Slide 10: Centro de Custo
            if dias_centro_custo:
                try:
                    analise_centro = insights_engine.gerar_analise_grafico('centro_custo', dias_centro_custo, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise centro custo: {e}")
                    analise_centro = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "centro_custo",
                    "titulo": "Dias Perdidos por Centro de Custo",
                    "subtitulo": "TOP 10 setores",
                    "dados": dias_centro_custo,
                    "analise": analise_centro
                })
            
            # Slide 11: Distribuição de Dias
            if distribuicao_dias:
                try:
                    analise_dist = insights_engine.gerar_analise_grafico('distribuicao_dias', distribuicao_dias, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise distribuição: {e}")
                    analise_dist = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "distribuicao_dias",
                    "titulo": "Distribuição de Dias por Atestado",
                    "subtitulo": "Histograma de frequência",
                    "dados": distribuicao_dias,
                    "analise": analise_dist
                })
            
            # Busca dados de produtividade (todos os meses para gráficos mês a mês) - APENAS CONVERPLAST
            try:
                produtividade_data = db.query(Produtividade).filter(
                    Produtividade.client_id == client_id
                ).order_by(Produtividade.mes_referencia.desc(), Produtividade.numero_tipo).all()
                
                if produtividade_data:
                    produtividade_todos = [
                        {
                            "numero_tipo": p.numero_tipo,
                            "tipo_consulta": p.tipo_consulta,
                            "ocupacionais": p.ocupacionais or 0,
                            "assistenciais": p.assistenciais or 0,
                            "acidente_trabalho": p.acidente_trabalho or 0,
                            "inss": p.inss or 0,
                            "sinistralidade": p.sinistralidade or 0,
                            "absenteismo": p.absenteismo or 0,
                            "pericia_indireta": p.pericia_indireta or 0,
                            "total": p.total or 0,
                            "mes_referencia": p.mes_referencia
                        }
                        for p in produtividade_data
                    ]
                    
                    try:
                        analise_prod = insights_engine.gerar_analise_grafico('produtividade', produtividade_todos, metricas) if hasattr(insights_engine, 'gerar_analise_grafico') else None
                    except Exception as e:
                        print(f"Erro ao gerar análise produtividade: {e}")
                        analise_prod = "Análise não disponível."
                    
                    slides.append({
                        "id": len(slides),
                        "tipo": "produtividade",
                        "titulo": "Produtividade",
                        "subtitulo": "Consultas realizadas - Anual (Mês a Mês)",
                        "dados": produtividade_todos,
                        "analise": analise_prod
                    })
            except Exception as e:
                print(f"Erro ao buscar produtividade: {e}")
            
            # Slide 12: Média por CID
            if media_cid:
                try:
                    analise_media = insights_engine.gerar_analise_grafico('media_cid', media_cid, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise média CID: {e}")
                    analise_media = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "media_cid",
                    "titulo": "Média de Dias por CID",
                    "subtitulo": "Doenças com maior média de dias",
                    "dados": media_cid,
                    "analise": analise_media
                })
            
            # Slide 13: Setor e Gênero
            if dias_setor_genero:
                try:
                    analise_setor_gen = insights_engine.gerar_analise_grafico('setor_genero', dias_setor_genero, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise setor/gênero: {e}")
                    analise_setor_gen = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "setor_genero",
                    "titulo": "Dias Perdidos por Setor e Gênero",
                    "subtitulo": "Comparativo entre gêneros por setor",
                    "dados": dias_setor_genero,
                    "analise": analise_setor_gen
                })
        
        # ==================== RODA DE OURO (client_id = 4) - ISOLADO ====================
        elif client_id == 4:
            # Slide 1: KPIs (RODA DE OURO) - primeiro slide após capa
            if metricas:
                try:
                    analise_kpis_ro = insights_engine.gerar_analise_grafico('kpis', None, metricas)
                except Exception as e:
                    print(f"Erro ao gerar análise KPIs RO: {e}")
                    analise_kpis_ro = "Análise não disponível."
                
                slides.append({
                    "id": len(slides),
                    "tipo": "kpis",
                    "titulo": "Indicadores Principais",
                    "subtitulo": "Visão geral do absenteísmo",
                    "dados": metricas,
                    "analise": analise_kpis_ro
                })
            
            try:
                classificacao_funcionarios_ro = analytics.classificacao_funcionarios_roda_ouro(client_id, 15, mes_inicio, mes_fim, funcionario, setor)
                if classificacao_funcionarios_ro:
                    try:
                        analise_func_ro = insights_engine.gerar_analise_grafico('classificacao_funcionarios_ro', classificacao_funcionarios_ro, metricas)
                    except Exception as e:
                        print(f"Erro ao gerar análise funcionários RO: {e}")
                        analise_func_ro = "Análise não disponível."
                    
                    slides.append({
                        "id": len(slides),
                        "tipo": "classificacao_funcionarios_ro",
                        "titulo": "Classificação por Funcionário",
                        "subtitulo": "Funcionários com mais dias de atestados",
                        "dados": classificacao_funcionarios_ro,
                        "analise": analise_func_ro
                    })
            except Exception as e:
                print(f"Erro ao calcular classificação funcionários RO para apresentação: {e}")
            
            try:
                classificacao_setores_ro = analytics.classificacao_setores_roda_ouro(client_id, 15, mes_inicio, mes_fim, funcionario, setor)
                if classificacao_setores_ro:
                    try:
                        analise_setores_ro = insights_engine.gerar_analise_grafico('classificacao_setores_ro', classificacao_setores_ro, metricas)
                    except Exception as e:
                        print(f"Erro ao gerar análise setores RO: {e}")
                        analise_setores_ro = "Análise não disponível."
                    
                    slides.append({
                        "id": len(slides),
                        "tipo": "classificacao_setores_ro",
                        "titulo": "Classificação por Setor",
                        "subtitulo": "Setores com mais dias de afastamento",
                        "dados": classificacao_setores_ro,
                        "analise": analise_setores_ro
                    })
            except Exception as e:
                print(f"Erro ao calcular classificação setores RO para apresentação: {e}")
            
            try:
                classificacao_doencas_ro = analytics.classificacao_doencas_roda_ouro(client_id, 15, mes_inicio, mes_fim, funcionario, setor)
                if classificacao_doencas_ro:
                    try:
                        analise_doencas_ro = insights_engine.gerar_analise_grafico('classificacao_doencas_ro', classificacao_doencas_ro, metricas)
                    except Exception as e:
                        print(f"Erro ao gerar análise doenças RO: {e}")
                        analise_doencas_ro = "Análise não disponível."
                    
                    slides.append({
                        "id": len(slides),
                        "tipo": "classificacao_doencas_ro",
                        "titulo": "Classificação por Doença",
                        "subtitulo": "Doenças x Dias de Afastamento",
                        "dados": classificacao_doencas_ro,
                        "analise": analise_doencas_ro
                    })
            except Exception as e:
                print(f"Erro ao calcular classificação doenças RO para apresentação: {e}")
            
            try:
                dias_ano_coerencia = analytics.dias_atestados_por_ano_coerencia(client_id, mes_inicio, mes_fim, funcionario, setor)
                if dias_ano_coerencia and (dias_ano_coerencia.get('anos') or dias_ano_coerencia.get('meses')):
                    try:
                        analise_dias_ano = insights_engine.gerar_analise_grafico('dias_ano_coerencia', dias_ano_coerencia, metricas)
                    except Exception as e:
                        print(f"Erro ao gerar análise dias ano: {e}")
                        analise_dias_ano = "Análise não disponível."
                    
                    slides.append({
                        "id": len(slides),
                        "tipo": "dias_ano_coerencia",
                        "titulo": "Dias Atestados por Ano",
                        "subtitulo": "Coerente vs Sem Coerência",
                        "dados": dias_ano_coerencia,
                        "analise": analise_dias_ano
                    })
            except Exception as e:
                print(f"Erro ao calcular dias ano coerência para apresentação: {e}")
            
            try:
                analise_coerencia = analytics.analise_atestados_coerencia(client_id, mes_inicio, mes_fim, funcionario, setor)
                if analise_coerencia and analise_coerencia.get('total', 0) > 0:
                    try:
                        analise_coer = insights_engine.gerar_analise_grafico('analise_coerencia', analise_coerencia, metricas)
                    except Exception as e:
                        print(f"Erro ao gerar análise coerência: {e}")
                        analise_coer = "Análise não disponível."
                    
                    slides.append({
                        "id": len(slides),
                        "tipo": "analise_coerencia",
                        "titulo": "Análise Atestados",
                        "subtitulo": "Coerente vs Sem Coerência",
                        "dados": analise_coerencia,
                        "analise": analise_coer
                    })
            except Exception as e:
                print(f"Erro ao calcular análise coerência para apresentação: {e}")
            
            try:
                tempo_servico_atestados = analytics.tempo_servico_atestados(client_id, mes_inicio, mes_fim, funcionario, setor)
                if tempo_servico_atestados and len(tempo_servico_atestados) > 0:
                    try:
                        analise_tempo = insights_engine.gerar_analise_grafico('tempo_servico_atestados', tempo_servico_atestados, metricas)
                    except Exception as e:
                        print(f"Erro ao gerar análise tempo serviço: {e}")
                        analise_tempo = "Análise não disponível."
                    
                    slides.append({
                        "id": len(slides),
                        "tipo": "tempo_servico_atestados",
                        "titulo": "Tempo Serviço x Atestados",
                        "subtitulo": "Análise por tempo de serviço na empresa",
                        "dados": tempo_servico_atestados,
                        "analise": analise_tempo
                    })
            except Exception as e:
                print(f"Erro ao calcular tempo serviço atestados para apresentação: {e}")
            
            # NOVOS SLIDES DE HORAS PERDIDAS (RODA DE OURO)
            try:
                horas_perdidas_genero = analytics.horas_perdidas_por_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
                if horas_perdidas_genero and len(horas_perdidas_genero) > 0:
                    try:
                        analise_horas_genero = insights_engine.gerar_analise_grafico('genero', horas_perdidas_genero, metricas)
                    except Exception as e:
                        print(f"Erro ao gerar análise horas por gênero: {e}")
                        analise_horas_genero = "Análise não disponível."
                    
                    slides.append({
                        "id": len(slides),
                        "tipo": "horas_perdidas_genero",
                        "titulo": "Horas Perdidas por Gênero",
                        "subtitulo": "Distribuição de horas perdidas (44h = 1 semana)",
                        "dados": horas_perdidas_genero,
                        "analise": analise_horas_genero
                    })
            except Exception as e:
                print(f"Erro ao calcular horas perdidas por gênero para apresentação: {e}")
            
            try:
                horas_perdidas_setor = analytics.horas_perdidas_por_setor(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
                if horas_perdidas_setor and len(horas_perdidas_setor) > 0:
                    try:
                        analise_horas_setor = insights_engine.gerar_analise_grafico('centro_custo', horas_perdidas_setor, metricas)
                    except Exception as e:
                        print(f"Erro ao gerar análise horas por setor: {e}")
                        analise_horas_setor = "Análise não disponível."
                    
                    slides.append({
                        "id": len(slides),
                        "tipo": "horas_perdidas_setor",
                        "titulo": "TOP 10 Setores - Horas Perdidas",
                        "subtitulo": "Setores com mais horas perdidas",
                        "dados": horas_perdidas_setor,
                        "analise": analise_horas_setor
                    })
            except Exception as e:
                print(f"Erro ao calcular horas perdidas por setor para apresentação: {e}")
            
            try:
                # Remove limite de meses para mostrar todos os meses disponíveis na planilha
                evolucao_mensal_horas = analytics.evolucao_mensal_horas(client_id, meses=0, mes_inicio=mes_inicio, mes_fim=mes_fim, funcionario=funcionario, setor=setor)
                if evolucao_mensal_horas and len(evolucao_mensal_horas) > 0:
                    try:
                        analise_evol_horas = insights_engine.gerar_analise_grafico('evolucao_mensal', evolucao_mensal_horas, metricas)
                    except Exception as e:
                        print(f"Erro ao gerar análise evolução horas: {e}")
                        analise_evol_horas = "Análise não disponível."
                    
                    slides.append({
                        "id": len(slides),
                        "tipo": "evolucao_mensal_horas",
                        "titulo": "Evolução Mensal de Horas Perdidas",
                        "subtitulo": "Tendência de horas perdidas ao longo do tempo",
                        "dados": evolucao_mensal_horas,
                        "analise": analise_evol_horas
                    })
            except Exception as e:
                print(f"Erro ao calcular evolução mensal horas para apresentação: {e}")
            
            try:
                comparativo_dias_horas_genero = analytics.comparativo_dias_horas_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
                if comparativo_dias_horas_genero and len(comparativo_dias_horas_genero) > 0:
                    try:
                        analise_comp = insights_engine.gerar_analise_grafico('setor_genero', comparativo_dias_horas_genero, metricas)
                    except Exception as e:
                        print(f"Erro ao gerar análise comparativo: {e}")
                        analise_comp = "Análise não disponível."
                    
                    slides.append({
                        "id": len(slides),
                        "tipo": "comparativo_dias_horas_genero",
                        "titulo": "Comparativo: Dias vs Horas vs Semanas",
                        "subtitulo": "Comparação por gênero",
                        "dados": comparativo_dias_horas_genero,
                        "analise": analise_comp
                    })
            except Exception as e:
                print(f"Erro ao calcular comparativo dias/horas por gênero para apresentação: {e}")
            
            try:
                analise_detalhada_genero = analytics.analise_detalhada_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
                if analise_detalhada_genero and analise_detalhada_genero.get('generos') and len(analise_detalhada_genero['generos']) > 0:
                    try:
                        analise_det = insights_engine.gerar_analise_grafico('genero', analise_detalhada_genero['generos'], metricas)
                    except Exception as e:
                        print(f"Erro ao gerar análise detalhada gênero: {e}")
                        analise_det = "Análise não disponível."
                    
                    slides.append({
                        "id": len(slides),
                        "tipo": "analise_detalhada_genero",
                        "titulo": "Análise Detalhada por Gênero",
                        "subtitulo": "Percentuais de dias, horas e registros",
                        "dados": analise_detalhada_genero,
                        "analise": analise_det
                    })
            except Exception as e:
                print(f"Erro ao calcular análise detalhada gênero para apresentação: {e}")
        
        # Slides de Ações (Intervenção Colaboradores)
        # Slide de introdução
        slides.append({
            "id": len(slides),
            "tipo": "acoes_intro",
            "titulo": "Intervenções Junto aos Colaboradores",
            "subtitulo": "Ações de Promoção de Saúde",
            "dados": {},
            "analise": ""
        })
        
        # Slide de Saúde Física
        slides.append({
            "id": len(slides),
            "tipo": "acoes_saude_fisica",
            "titulo": "Saúde Física",
            "subtitulo": "Promoção da saúde preventiva e autocuidado",
            "dados": {},
            "analise": ""
        })
        
        # Slide de Saúde Emocional
        slides.append({
            "id": len(slides),
            "tipo": "acoes_saude_emocional",
            "titulo": "Saúde Emocional",
            "subtitulo": "Bem-estar emocional e resiliência",
            "dados": {},
            "analise": ""
        })
        
        # Slide de Saúde Social
        slides.append({
            "id": len(slides),
            "tipo": "acoes_saude_social",
            "titulo": "Saúde Social",
            "subtitulo": "Relações interpessoais e clima organizacional",
            "dados": {},
            "analise": ""
        })
        
        tempo_total = time.time() - inicio
        print(f"[APRESENTACAO] ===== FIM - Total de slides: {len(slides)} - Tempo: {tempo_total:.2f}s =====")
        
        return {
            "slides": slides,
            "total_slides": len(slides)
        }
        
    except Exception as e:
        import traceback
        print(f"[APRESENTACAO] ===== ERRO =====")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar apresentação: {str(e)}")

@app.get("/api/preview/{upload_id}")
async def preview_data(
    upload_id: int,
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório para validação
    page: int = 1,
    current_user: User = Depends(get_current_active_user),
    per_page: int = 50,
    db: Session = Depends(get_db)
):
    """Preview dos dados do upload"""
    # Valida client_id
    validar_client_id(db, client_id)
    
    # Valida se o upload pertence ao cliente
    upload = db.query(Upload).filter(
        Upload.id == upload_id,
        Upload.client_id == client_id
    ).first()
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload não encontrado ou não pertence ao cliente")
    
    offset = (page - 1) * per_page
    
    atestados = db.query(Atestado).filter(Atestado.upload_id == upload_id).offset(offset).limit(per_page).all()
    total = db.query(Atestado).filter(Atestado.upload_id == upload_id).count()
    
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "dados": [
            {
                "id": a.id,
                "nome_funcionario": a.nome_funcionario,
                "setor": a.setor,
                "cargo": a.cargo,
                "genero": a.genero,
                "data_afastamento": a.data_afastamento.isoformat() if a.data_afastamento else None,
                "data_retorno": a.data_retorno.isoformat() if a.data_retorno else None,
                "tipo_atestado": a.tipo_atestado,
                "cid": a.cid,
                "descricao_cid": a.descricao_cid,
                "dias_perdidos": a.dias_perdidos,
                "horas_perdidas": a.horas_perdidas
            }
            for a in atestados
        ]
    }

@app.get("/api/analises/funcionarios")
async def analise_funcionarios(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Análise por funcionários"""
    # Valida client_id
    validar_client_id(db, client_id)
    
    analytics = Analytics(db)
    return analytics.top_funcionarios(client_id, 1000, mes_inicio, mes_fim)

@app.get("/api/analises/setores")
async def analise_setores(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Análise por setores"""
    # Valida client_id
    validar_client_id(db, client_id)
    
    analytics = Analytics(db)
    return analytics.top_setores(client_id, 20, mes_inicio, mes_fim)

@app.get("/api/analises/cids")
async def analise_cids(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Análise por CIDs"""
    # Valida client_id
    validar_client_id(db, client_id)
    
    analytics = Analytics(db)
    return analytics.top_cids(client_id, 20, mes_inicio, mes_fim)

@app.get("/api/tendencias")
async def tendencias(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Análise de tendências"""
    # Valida client_id
    validar_client_id(db, client_id)
    
    analytics = Analytics(db)
    evolucao = analytics.evolucao_mensal(client_id, 12)
    
    # Calcula tendência simples (média móvel)
    if len(evolucao) >= 3:
        ultimos_3 = evolucao[-3:]
        media_recente = sum(m['quantidade'] for m in ultimos_3) / 3
        
        primeiros_3 = evolucao[:3]
        media_antiga = sum(m['quantidade'] for m in primeiros_3) / 3
        
        tendencia = "crescente" if media_recente > media_antiga else "decrescente" if media_recente < media_antiga else "estável"
    else:
        tendencia = "insuficiente"
    
    return {
        "evolucao": evolucao,
        "tendencia": tendencia,
        "analise": "Análise de tendências com base nos últimos 12 meses"
    }

# Endpoint duplicado removido - usando o endpoint completo abaixo

@app.delete("/api/uploads/{upload_id}")
async def delete_upload(
    upload_id: int,
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório para validação
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deleta um upload e seus dados"""
    # Valida client_id
    validar_client_id(db, client_id)
    
    # Valida se o upload pertence ao cliente
    upload = db.query(Upload).filter(
        Upload.id == upload_id,
        Upload.client_id == client_id
    ).first()
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload não encontrado ou não pertence ao cliente")
    
    db.delete(upload)
    db.commit()
    
    return {"success": True, "message": "Upload deletado com sucesso"}

# ==================== ROUTES - EXPORTS ====================

# Função helper para buscar dados EXATAMENTE como o dashboard
def buscar_dados_dashboard_completo(
    client_id: int,
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    funcionario: Optional[List[str]] = None,
    setor: Optional[List[str]] = None,
    db: Session = None
):
    """Busca TODOS os dados exatamente como o endpoint /api/dashboard faz"""
    analytics = Analytics(db)
    insights_engine = InsightsEngine(db)
    
    # REPLICA EXATAMENTE A LÓGICA DO DASHBOARD
    try:
        metricas = analytics.metricas_gerais(client_id, mes_inicio, mes_fim, funcionario, setor)
    except Exception as e:
        print(f"Erro ao calcular métricas gerais: {e}")
        metricas = {
            "total_atestados_dias": 0,
            "total_dias_perdidos": 0,
            "total_horas_perdidas": 0
        }
    
    try:
        top_cids = analytics.top_cids(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
    except Exception as e:
        print(f"Erro ao calcular top CIDs: {e}")
        top_cids = []
    
    try:
        top_setores = analytics.top_setores(client_id, 5, mes_inicio, mes_fim, funcionario, setor)
    except Exception as e:
        print(f"Erro ao calcular top setores: {e}")
        top_setores = []
    
    try:
        evolucao = analytics.evolucao_mensal(client_id, 12, mes_inicio, mes_fim, funcionario, setor)
    except Exception as e:
        print(f"Erro ao calcular evolução mensal: {e}")
        evolucao = []
    
    try:
        distribuicao_genero = analytics.distribuicao_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
    except Exception as e:
        print(f"Erro ao calcular distribuição de gênero: {e}")
        distribuicao_genero = []
    
    try:
        top_funcionarios = analytics.top_funcionarios(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
    except Exception as e:
        print(f"Erro ao calcular top funcionários: {e}")
        top_funcionarios = []
    
    try:
        top_escalas = analytics.top_escalas(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
    except Exception as e:
        print(f"Erro ao calcular top escalas: {e}")
        top_escalas = []
    
    try:
        top_motivos = analytics.top_motivos(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
    except Exception as e:
        print(f"Erro ao calcular top motivos: {e}")
        top_motivos = []
    
    try:
        dias_centro_custo = analytics.dias_perdidos_por_centro_custo(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
    except Exception as e:
        print(f"Erro ao calcular dias por centro de custo: {e}")
        dias_centro_custo = []
    
    try:
        distribuicao_dias = analytics.distribuicao_dias_por_atestado(client_id, mes_inicio, mes_fim, funcionario, setor)
    except Exception as e:
        print(f"Erro ao calcular distribuição de dias: {e}")
        distribuicao_dias = []
    
    try:
        media_cid = analytics.media_dias_por_cid(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
    except Exception as e:
        print(f"Erro ao calcular média por CID: {e}")
        media_cid = []
    
    try:
        top_cids_dias = analytics.top_cids(client_id, 5, mes_inicio, mes_fim, funcionario, setor)
    except Exception as e:
        print(f"Erro ao calcular top CIDs para dias: {e}")
        top_cids_dias = []
    
    try:
        dias_setor_genero = analytics.dias_perdidos_setor_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
    except Exception as e:
        print(f"Erro ao calcular dias por setor e gênero: {e}")
        dias_setor_genero = []
    
    # Busca insights gerais
    insights = []
    try:
        insights = insights_engine.gerar_insights(client_id)
    except Exception as e:
        print(f"Erro ao gerar insights gerais: {e}")
        insights = []
    
    # Dados específicos para Roda de Ouro (APENAS para client_id = 4)
    classificacao_funcionarios_ro = []
    classificacao_setores_ro = []
    classificacao_doencas_ro = []
    dias_ano_coerencia = {'anos': [], 'coerente': [], 'sem_coerencia': []}
    analise_coerencia = {'coerente': 0, 'sem_coerencia': 0, 'total': 0, 'percentual_coerente': 0, 'percentual_sem_coerencia': 0}
    tempo_servico_atestados = []
    horas_perdidas_genero = []
    horas_perdidas_setor = []
    evolucao_mensal_horas = []
    analise_detalhada_genero_data = {}
    comparativo_dias_horas_genero_data = []
    horas_perdidas_setor_genero_data = []
    
    # Só calcula se for Roda de Ouro (ID = 4)
    if client_id == 4:
        try:
            classificacao_funcionarios_ro = analytics.classificacao_funcionarios_roda_ouro(client_id, 15, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular classificação funcionários RO: {e}")
        
        try:
            classificacao_setores_ro = analytics.classificacao_setores_roda_ouro(client_id, 15, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular classificação setores RO: {e}")
            classificacao_setores_ro = []
        
        try:
            classificacao_doencas_ro = analytics.classificacao_doencas_roda_ouro(client_id, 15, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular classificação doenças RO: {e}")
        
        try:
            dias_ano_coerencia = analytics.dias_atestados_por_ano_coerencia(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular dias por ano coerência: {e}")
        
        try:
            analise_coerencia = analytics.analise_atestados_coerencia(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular análise coerência: {e}")
        
        try:
            tempo_servico_atestados = analytics.tempo_servico_atestados(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular tempo serviço: {e}")
        
        try:
            horas_perdidas_genero = analytics.horas_perdidas_por_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular horas perdidas por gênero: {e}")
        
        try:
            horas_perdidas_setor = analytics.horas_perdidas_por_setor(client_id, 10, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular horas perdidas por setor: {e}")
        
        try:
            evolucao_mensal_horas = analytics.evolucao_mensal_horas(client_id, meses=0, mes_inicio=mes_inicio, mes_fim=mes_fim, funcionario=funcionario, setor=setor)
        except Exception as e:
            print(f"Erro ao calcular evolução mensal de horas: {e}")
        
        try:
            analise_detalhada_genero_data = analytics.analise_detalhada_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular análise detalhada por gênero: {e}")
        
        try:
            comparativo_dias_horas_genero_data = analytics.comparativo_dias_horas_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular comparativo dias/horas por gênero: {e}")
        
        try:
            horas_perdidas_setor_genero_data = analytics.horas_perdidas_setor_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular horas perdidas por setor e gênero: {e}")
    
    # Adiciona análises de todos os gráficos
    tipos_graficos = [
        ('top_cids', top_cids, '📊', 'TOP 10 Doenças Mais Frequentes'),
        ('funcionarios_dias', top_funcionarios, '👤', 'Dias Perdidos por Funcionário'),
        ('evolucao_mensal', evolucao, '📈', 'Evolução Mensal'),
        ('top_setores', top_setores, '🏢', 'TOP 5 Setores'),
        ('genero', distribuicao_genero, '👥', 'Distribuição por Gênero'),
        ('dias_doenca', top_cids_dias, '🩺', 'Dias por Doença'),
        ('escalas', top_escalas, '⏰', 'Escalas com Mais Atestados'),
        ('motivos', top_motivos, '📋', 'Motivos de Incidência'),
        ('centro_custo', dias_centro_custo, '💰', 'Dias Perdidos por Centro de Custo'),
        ('distribuicao_dias', distribuicao_dias, '📊', 'Distribuição de Dias por Atestado'),
        ('media_cid', media_cid, '📊', 'Média de Dias por CID'),
        ('setor_genero', dias_setor_genero, '👥', 'Dias Perdidos por Setor e Gênero'),
    ]
    
    for tipo_grafico, dados_grafico, icone, titulo in tipos_graficos:
        if dados_grafico:
            try:
                analise = insights_engine.gerar_analise_grafico(tipo_grafico, dados_grafico, metricas)
                if analise:
                    partes = analise.split('💡')
                    insights.append({
                        'tipo': 'analise',
                        'icone': icone,
                        'titulo': f'Análise: {titulo}',
                        'descricao': partes[0].strip().replace('**', '') if len(partes) > 0 else analise.replace('**', ''),
                        'recomendacao': partes[1].strip().replace('**', '').replace('💡', '').replace('Recomendação:', '').strip() if len(partes) > 1 else None
                    })
            except Exception as e:
                print(f"Erro ao gerar análise para {tipo_grafico}: {e}")
    
    # Adiciona análises específicas da Roda de Ouro
    if client_id == 4:
        tipos_graficos_ro = [
            ('classificacao_funcionarios_ro', classificacao_funcionarios_ro, '👤', 'Classificação por Funcionário'),
            ('classificacao_setores_ro', classificacao_setores_ro, '🏢', 'Classificação por Setor'),
            ('classificacao_doencas_ro', classificacao_doencas_ro, '🩺', 'Classificação por Doença'),
            ('dias_ano_coerencia', dias_ano_coerencia, '📅', 'Dias Atestados por Ano'),
            ('analise_coerencia', analise_coerencia, '✅', 'Análise Atestados'),
            ('tempo_servico_atestados', tempo_servico_atestados, '⏱️', 'Tempo Serviço x Atestados'),
            ('horas_perdidas_genero', horas_perdidas_genero, '👥', 'Horas Perdidas por Gênero'),
            ('horas_perdidas_setor', horas_perdidas_setor, '🏢', 'Horas Perdidas por Setor'),
            ('evolucao_mensal_horas', evolucao_mensal_horas, '📈', 'Evolução Mensal de Horas Perdidas'),
            ('comparativo_dias_horas_genero', comparativo_dias_horas_genero_data, '📊', 'Comparativo: Dias vs Horas vs Semanas'),
            ('horas_perdidas_setor_genero', horas_perdidas_setor_genero_data, '👥', 'Horas Perdidas por Setor e Gênero'),
            ('analise_detalhada_genero', analise_detalhada_genero_data, '📊', 'Análise Detalhada por Gênero')
        ]
        
        for tipo_grafico, dados_grafico, icone, titulo in tipos_graficos_ro:
            if dados_grafico and (isinstance(dados_grafico, list) and len(dados_grafico) > 0 or isinstance(dados_grafico, dict) and dados_grafico):
                try:
                    analise = insights_engine.gerar_analise_grafico(tipo_grafico, dados_grafico, metricas)
                    if analise:
                        partes = analise.split('💡')
                        insights.append({
                            'tipo': 'analise',
                            'icone': icone,
                            'titulo': f'Análise: {titulo}',
                            'descricao': partes[0].strip().replace('**', '') if len(partes) > 0 else analise.replace('**', ''),
                            'recomendacao': partes[1].strip().replace('**', '').replace('💡', '').replace('Recomendação:', '').strip() if len(partes) > 1 else None
                        })
                except Exception as e:
                    print(f"Erro ao gerar análise para {tipo_grafico}: {e}")
    
    # Retorna todos os dados
    dados_relatorio = {
        'top_cids': top_cids,
        'top_funcionarios': top_funcionarios,
        'top_setores': top_setores,
        'evolucao_mensal': evolucao,
        'distribuicao_genero': distribuicao_genero,
        'top_escalas': top_escalas,
        'top_motivos': top_motivos,
        'dias_centro_custo': dias_centro_custo,
        'distribuicao_dias': distribuicao_dias,
        'media_cid': media_cid,
        'top_cids_dias': top_cids_dias,
        'dias_setor_genero': dias_setor_genero
    }
    
    # Adiciona dados específicos da Roda de Ouro
    if client_id == 4:
        dados_relatorio.update({
            'classificacao_funcionarios_ro': classificacao_funcionarios_ro,
            'classificacao_setores_ro': classificacao_setores_ro,
            'classificacao_doencas_ro': classificacao_doencas_ro,
            'dias_ano_coerencia': dias_ano_coerencia,
            'analise_coerencia': analise_coerencia,
            'tempo_servico_atestados': tempo_servico_atestados,
            'horas_perdidas_genero': horas_perdidas_genero,
            'horas_perdidas_setor': horas_perdidas_setor,
            'evolucao_mensal_horas': evolucao_mensal_horas,
            'comparativo_dias_horas_genero': comparativo_dias_horas_genero_data,
            'horas_perdidas_setor_genero': horas_perdidas_setor_genero_data,
            'analise_detalhada_genero': analise_detalhada_genero_data
        })
    
    return {
        'metricas': metricas,
        'dados_relatorio': dados_relatorio,
        'insights': insights,
        'insights_engine': insights_engine
    }

@app.get("/api/export/excel")
async def export_excel(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    mes: Optional[str] = None,
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    upload_id: Optional[int] = None,
    funcionario: Optional[List[str]] = Query(None),
    setor: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Exporta relatório completo para Excel - USA DADOS EXATOS DO DASHBOARD"""
    try:
        # Valida client_id
        print(f"[EXPORT EXCEL] Recebido client_id: {client_id}")
        client = validar_client_id(db, client_id)
        print(f"[EXPORT EXCEL] Cliente encontrado: {client.nome} (ID: {client.id})")
        
        # USA DADOS EXATOS DO DASHBOARD
        print(f"[EXPORT EXCEL] Buscando dados do dashboard para replicar nos relatórios...")
        dados_completos = buscar_dados_dashboard_completo(
            client_id, mes_inicio, mes_fim, funcionario, setor, db
        )
        
        metricas_gerais = dados_completos['metricas']
        dados_relatorio = dados_completos['dados_relatorio']
        
        # Usa ReportGenerator para Excel (ainda necessário)
        if ReportGenerator is None:
            raise HTTPException(status_code=500, detail="ReportGenerator não disponível")
        report_gen = ReportGenerator(db=db, client_id=client_id)
        
        # Busca dados completos para Excel (todos os atestados)
        query = db.query(Atestado).join(Upload).filter(Upload.client_id == client_id)
        if upload_id:
            query = query.filter(Upload.id == upload_id)
        elif mes:
            query = query.filter(Upload.mes_referencia == mes)
        elif mes_inicio and mes_fim:
            query = query.filter(Upload.mes_referencia >= mes_inicio, Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros de funcionário e setor se fornecidos
        if funcionario:
            query = query.filter(Atestado.nomecompleto.in_(funcionario))
        if setor:
            query = query.filter(Atestado.setor.in_(setor))
        
        atestados = query.all()
        
        if not atestados:
            raise HTTPException(status_code=404, detail="Nenhum dado encontrado")
        
        # Converter para lista de dicionários
        dados = []
        for a in atestados:
            dados.append({
                'Nome': a.nomecompleto or a.nome_funcionario,
                'Setor': a.setor,
                'CID': a.cid,
                'Diagnóstico': a.diagnostico or a.descricao_cid,
                'Dias Atestados': a.dias_atestados or 0,
                'Horas Perdidas': a.horas_perdi or 0,
                'Motivo': a.motivo_atestado,
                'Escala': a.escala,
            })
        
        # Gerar arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_absenteismo_{timestamp}.xlsx"
        filepath = os.path.join(EXPORTS_DIR, filename)
        
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        
        # Usar gerador de relatórios
        periodo = f"{mes_inicio} a {mes_fim}" if mes_inicio and mes_fim else (mes or "Todos os períodos")
        success = report_gen.generate_excel_report(filepath, dados, metricas_gerais, dados_relatorio, periodo, client_id=client_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Erro ao gerar relatório Excel")
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao exportar: {str(e)}")

# Rota de exportação PDF REMOVIDA

@app.get("/api/export/pptx")
async def export_pptx(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    mes: Optional[str] = None,
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    upload_id: Optional[int] = None,
    funcionario: Optional[List[str]] = Query(None),
    setor: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Exporta apresentação completa para PowerPoint - USA DADOS EXATOS DO DASHBOARD"""
    try:
        # Valida client_id
        print(f"[EXPORT PPTX] Recebido client_id: {client_id}")
        client = validar_client_id(db, client_id)
        print(f"[EXPORT PPTX] Cliente encontrado: {client.nome} (ID: {client.id})")
        
        # USA DADOS EXATOS DO DASHBOARD
        print(f"[EXPORT PPTX] Buscando dados do dashboard para replicar nos relatórios...")
        dados_completos = buscar_dados_dashboard_completo(
            client_id, mes_inicio, mes_fim, funcionario, setor, db
        )
        
        metricas_gerais = dados_completos['metricas']
        dados_relatorio = dados_completos['dados_relatorio']
        insights = dados_completos['insights']
        insights_engine = dados_completos['insights_engine']
        
        # Usa ReportGenerator para PPTX (ainda necessário)
        if ReportGenerator is None:
            raise HTTPException(status_code=500, detail="ReportGenerator não disponível")
        report_gen = ReportGenerator(db=db, client_id=client_id)
        
        # Gerar arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"apresentacao_absenteismo_{timestamp}.pptx"
        filepath = os.path.join(EXPORTS_DIR, filename)
        
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        
        # Gerar período
        periodo = f"{mes_inicio} a {mes_fim}" if mes_inicio and mes_fim else (mes or "Todos os períodos")
        
        # Gerar PowerPoint com gráficos e insights
        success = report_gen.generate_powerpoint_report(filepath, dados_relatorio, metricas_gerais, insights, periodo, insights_engine, client_id=client_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Erro ao gerar relatório PowerPoint")
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation'
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao exportar: {str(e)}")

# ==================== ROUTES - COMPARATIVOS ====================

@app.get("/api/relatorios/comparativo")
async def comparativo_periodos(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    periodo1_inicio: str = Query(...),
    periodo1_fim: str = Query(...),
    periodo2_inicio: str = Query(...),
    periodo2_fim: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Compara dois períodos e retorna métricas e variações"""
    try:
        # Valida client_id
        validar_client_id(db, client_id)
        
        analytics = Analytics(db)
        
        # Busca métricas do período 1
        metricas_p1 = analytics.metricas_gerais(client_id, periodo1_inicio, periodo1_fim, None, None)
        
        # Busca métricas do período 2
        metricas_p2 = analytics.metricas_gerais(client_id, periodo2_inicio, periodo2_fim, None, None)
        
        # Calcula variações percentuais
        def calcular_variacao(valor1, valor2):
            if valor1 == 0:
                return 100.0 if valor2 > 0 else 0.0
            return ((valor2 - valor1) / valor1) * 100
        
        variacoes = {
            'atestados': calcular_variacao(
                metricas_p1.get('total_atestados', 0),
                metricas_p2.get('total_atestados', 0)
            ),
            'dias': calcular_variacao(
                metricas_p1.get('total_dias_perdidos', 0),
                metricas_p2.get('total_dias_perdidos', 0)
            ),
            'horas': calcular_variacao(
                metricas_p1.get('total_horas_perdidas', 0),
                metricas_p2.get('total_horas_perdidas', 0)
            ),
            'taxa': calcular_variacao(
                metricas_p1.get('total_atestados', 0) or 1,
                metricas_p2.get('total_atestados', 0) or 1
            )
        }
        
        # Formata resposta
        resultado = {
            'periodo1': {
                'inicio': periodo1_inicio,
                'fim': periodo1_fim,
                'total_atestados': metricas_p1.get('total_atestados', 0),
                'total_atestados_dias': metricas_p1.get('total_atestados_dias', 0),
                'total_atestados_horas': metricas_p1.get('total_atestados_horas', 0),
                'total_dias_perdidos': metricas_p1.get('total_dias_perdidos', 0),
                'total_horas_perdidas': metricas_p1.get('total_horas_perdidas', 0),
            },
            'periodo2': {
                'inicio': periodo2_inicio,
                'fim': periodo2_fim,
                'total_atestados': metricas_p2.get('total_atestados', 0),
                'total_atestados_dias': metricas_p2.get('total_atestados_dias', 0),
                'total_atestados_horas': metricas_p2.get('total_atestados_horas', 0),
                'total_dias_perdidos': metricas_p2.get('total_dias_perdidos', 0),
                'total_horas_perdidas': metricas_p2.get('total_horas_perdidas', 0),
            },
            'variacoes': variacoes
        }
        
        return resultado
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar comparativo: {str(e)}")

# ==================== ROUTES - PERFIL FUNCIONÁRIO ====================

@app.get("/perfil_funcionario", response_class=HTMLResponse)
async def perfil_funcionario_page():
    """Página de perfil de funcionário"""
    file_path = os.path.join(FRONTEND_DIR, "perfil_funcionario.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/funcionario/perfil")
async def perfil_funcionario(
    nome: str = Query(...),
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório - sem valor padrão
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retorna perfil completo de um funcionário"""
    try:
        # Valida client_id
        validar_client_id(db, client_id)
        
        analytics = Analytics(db)
        
        # Busca todos os atestados do funcionário
        query = db.query(Atestado).join(Upload).filter(
            Upload.client_id == client_id,
            (Atestado.nomecompleto == nome) | (Atestado.nome_funcionario == nome)
        ).order_by(Upload.mes_referencia.desc(), Atestado.id.desc())
        
        atestados = query.all()
        
        if not atestados:
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")
        
        # Primeiro registro para pegar informações gerais
        primeiro = atestados[0]
        
        # Calcula totais
        total_atestados = len(atestados)
        total_dias = sum(a.dias_atestados or 0 for a in atestados)
        total_horas = sum(a.horas_perdi or 0 for a in atestados)
        media_dias = total_dias / total_atestados if total_atestados > 0 else 0
        
        # Evolução mensal
        evolucao_mensal = {}
        for a in atestados:
            # Busca o upload relacionado
            upload = db.query(Upload).filter(Upload.id == a.upload_id).first()
            mes = upload.mes_referencia if upload else None
            if mes:
                if mes not in evolucao_mensal:
                    evolucao_mensal[mes] = {'dias_perdidos': 0, 'quantidade': 0}
                evolucao_mensal[mes]['dias_perdidos'] += a.dias_atestados or 0
                evolucao_mensal[mes]['quantidade'] += 1
        
        evolucao_lista = [{'mes': mes, 'dias_perdidos': dados['dias_perdidos'], 'quantidade': dados['quantidade']} 
                         for mes, dados in sorted(evolucao_mensal.items())]
        
        # TOP CIDs
        cids_count = {}
        for a in atestados:
            cid = a.cid or 'N/A'
            if cid not in cids_count:
                cids_count[cid] = {
                    'cid': cid,
                    'descricao': a.diagnostico or a.descricao_cid or '',
                    'quantidade': 0,
                    'dias_perdidos': 0
                }
            cids_count[cid]['quantidade'] += 1
            cids_count[cid]['dias_perdidos'] += a.dias_atestados or 0
        
        top_cids = sorted(cids_count.values(), key=lambda x: x['quantidade'], reverse=True)
        
        # Histórico
        historico = []
        for a in atestados[:50]:  # Últimos 50 registros
            # Busca o upload relacionado
            upload = db.query(Upload).filter(Upload.id == a.upload_id).first()
            historico.append({
                'data_afastamento': a.data_afastamento.strftime('%d/%m/%Y') if a.data_afastamento else None,
                'mes_referencia': upload.mes_referencia if upload else None,
                'cid': a.cid,
                'diagnostico': a.diagnostico or a.descricao_cid,
                'descricao': a.descricao_cid,
                'dias_atestados': a.dias_atestados or 0,
                'horas_perdi': a.horas_perdi or 0,
                'motivo_atestado': a.motivo_atestado,
                'setor': a.setor
            })
        
        return {
            'nome': primeiro.nomecompleto or primeiro.nome_funcionario or nome,
            'setor': primeiro.setor,
            'genero': primeiro.genero,
            'total_atestados': total_atestados,
            'total_dias_perdidos': total_dias,
            'total_horas_perdidas': total_horas,
            'media_dias_per_atestado': media_dias,
            'total_registros': total_atestados,
            'evolucao_mensal': evolucao_lista,
            'top_cids': top_cids,
            'historico': historico
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar perfil: {str(e)}")

# ==================== ROUTES - GESTÃO DE DADOS ====================

@app.get("/api/dados/todos")
async def listar_todos_dados(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    upload_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista todos os dados com filtros"""
    try:
        # Valida client_id
        validar_client_id(db, client_id)
        
        query = db.query(Atestado).join(Upload).filter(Upload.client_id == client_id)
        
        if upload_id:
            query = query.filter(Upload.id == upload_id)
        
        # Ordena por data_afastamento, mas trata caso seja None
        try:
            # Usa nullslast para colocar None no final
            atestados = query.order_by(nullslast(desc(Atestado.data_afastamento))).all()
        except Exception as e:
            print(f"Erro na ordenação, tentando sem ordenação: {e}")
            # Se houver erro na ordenação, tenta sem ordenação
            atestados = query.all()
        
        # Estatísticas - usa os novos campos da planilha padronizada
        estatisticas = {
            'total_registros': len(atestados),
            'total_atestados_dias': sum((a.dias_atestados or 0) for a in atestados),  # Soma dos dias_atestados
            'total_dias_perdidos': sum((a.dias_atestados or 0) for a in atestados)  # Mesmo valor de total_atestados_dias
        }
        
        # Dados - inclui todas as colunas originais da planilha
        dados = []
        todas_colunas_ordenadas = []  # Lista ordenada para manter ordem
        todas_colunas_set = set()  # Set para verificar se já adicionou
        
        for a in atestados:
            try:
                # Parse dos dados originais (JSON)
                # Usa object_pairs_hook para manter ordem
                dados_originais = {}
                if a.dados_originais:
                    try:
                        # Parse JSON mantendo ordem (Python 3.7+ mantém ordem, mas garantimos)
                        dados_originais = json.loads(a.dados_originais, object_pairs_hook=OrderedDict)
                        if isinstance(dados_originais, dict):
                            # Adiciona colunas na ordem que aparecem no dict (ordem original da planilha)
                            for col in dados_originais.keys():
                                if col not in todas_colunas_set:
                                    todas_colunas_ordenadas.append(col)
                                    todas_colunas_set.add(col)
                    except Exception as e:
                        print(f"Erro ao parse JSON dados_originais: {e}")
                        dados_originais = {}
                
                # Busca o upload para pegar mes_referencia
                upload = db.query(Upload).filter(Upload.id == a.upload_id).first()
                
                # Cria registro com os novos campos da planilha padronizada
                registro = {
                    'id': a.id,
                    'upload_id': a.upload_id,
                    'mes_referencia': upload.mes_referencia if upload else None,
                    # Campos principais da planilha padronizada
                    'nomecompleto': a.nomecompleto or '',
                    'descricao_atestad': a.descricao_atestad or '',
                    'dias_atestados': float(a.dias_atestados) if a.dias_atestados else 0,
                    'cid': a.cid or '',
                    'diagnostico': a.diagnostico or '',
                    'centro_custo': a.centro_custo or '',
                    'setor': a.setor or '',
                    'motivo_atestado': a.motivo_atestado or '',
                    'escala': a.escala or '',
                    'horas_dia': float(a.horas_dia) if a.horas_dia else 0,
                    'horas_perdi': float(a.horas_perdi) if a.horas_perdi else 0,
                    # Campos legados (para compatibilidade)
                    'nome_funcionario': a.nome_funcionario or a.nomecompleto or '',
                    'cpf': a.cpf or '',
                    'matricula': a.matricula or '',
                    'cargo': a.cargo or '',
                    'genero': a.genero or '',
                    'data_afastamento': a.data_afastamento.isoformat() if a.data_afastamento else None,
                    'data_retorno': a.data_retorno.isoformat() if a.data_retorno else None,
                    'tipo_info_atestado': a.tipo_info_atestado,
                    'tipo_atestado': a.tipo_atestado or '',
                    'descricao_cid': a.descricao_cid or a.diagnostico or '',
                    'numero_dias_atestado': float(a.numero_dias_atestado) if a.numero_dias_atestado else (float(a.dias_atestados) if a.dias_atestados else 0),
                    'numero_horas_atestado': float(a.numero_horas_atestado) if a.numero_horas_atestado else (float(a.horas_dia) if a.horas_dia else 0),
                    'dias_perdidos': float(a.dias_perdidos) if a.dias_perdidos else (float(a.dias_atestados) if a.dias_atestados else 0),
                    'horas_perdidas': float(a.horas_perdidas) if a.horas_perdidas else (float(a.horas_perdi) if a.horas_perdi else 0),
                }
                
                # Adiciona TODAS as colunas originais da planilha na ordem original
                # Usa OrderedDict para garantir ordem
                registro_final = OrderedDict()
                
                # Adiciona colunas originais PRIMEIRO na ordem que aparecem (ordem da planilha)
                for col_original in dados_originais.keys():
                    registro_final[col_original] = dados_originais[col_original]
                
                # Depois adiciona campos processados (para compatibilidade)
                for key in registro.keys():
                    if key != 'dados_originais' and key not in registro_final:
                        registro_final[key] = registro[key]
                
                dados.append(dict(registro_final))  # Converte para dict normal
            except Exception as e:
                print(f"Erro ao processar registro {a.id}: {e}")
                continue
        
        # ORDEM EXATA DA PLANILHA - usa a ordem que veio dos dados originais
        # Se não tiver colunas originais, usa a ordem padrão
        if todas_colunas_ordenadas:
            # Usa a ordem que veio dos dados originais (primeira ocorrência)
            todas_colunas_list = todas_colunas_ordenadas
        else:
            # Fallback para ordem padrão
            todas_colunas_list = [
                'nomecompleto',      # 1. NOMECOMPLETO
                'descricao_atestad', # 2. DESCRIÇÃO ATESTAD
                'dias_atestados',    # 3. DIAS ATESTADOS
                'cid',               # 4. CID
                'diagnostico',       # 5. DIAGNÓSTICO
                'centro_custo',      # 6. CENTROCUST
                'setor',             # 7. setor
                'motivo_atestado',   # 8. motivo atestado
                'escala',            # 9. escala
                'horas_dia',         # 10. Horas/dia
                'horas_perdi'        # 11. Horas perdi
            ]
        
        resultado = {
            'dados': dados,
            'estatisticas': estatisticas,
            'colunas_originais': todas_colunas_list  # Lista de todas as colunas da planilha
        }
        
        return corrigir_encoding_json(resultado)
        
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao carregar dados: {error_detail}")

@app.get("/api/dados/{atestado_id}")
async def obter_dado(
    atestado_id: int,
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório para validação
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtém um registro específico"""
    # Valida client_id
    validar_client_id(db, client_id)
    
    # Busca atestado e valida que pertence ao cliente
    atestado = db.query(Atestado).join(Upload).filter(
        Atestado.id == atestado_id,
        Upload.client_id == client_id
    ).first()
    
    if not atestado:
        raise HTTPException(status_code=404, detail="Registro não encontrado ou não pertence ao cliente")
    
    return corrigir_encoding_json({
        'id': atestado.id,
        'upload_id': atestado.upload_id,
        'nome_funcionario': atestado.nome_funcionario,
        'cpf': atestado.cpf,
        'matricula': atestado.matricula,
        'setor': atestado.setor,
        'cargo': atestado.cargo,
        'genero': atestado.genero,
        'data_afastamento': atestado.data_afastamento.isoformat() if atestado.data_afastamento else None,
        'data_retorno': atestado.data_retorno.isoformat() if atestado.data_retorno else None,
        'tipo_info_atestado': atestado.tipo_info_atestado,
        'tipo_atestado': atestado.tipo_atestado,
        'cid': atestado.cid,
        'descricao_cid': atestado.descricao_cid,
        'numero_dias_atestado': atestado.numero_dias_atestado,
        'numero_horas_atestado': atestado.numero_horas_atestado,
        'dias_perdidos': atestado.dias_perdidos,
        'horas_perdidas': atestado.horas_perdidas
    })

@app.post("/api/dados")
async def criar_dado(
    atestado: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Cria um novo registro"""
    try:
        novo = Atestado(**atestado)
        db.add(novo)
        db.commit()
        db.refresh(novo)
        
        return {"success": True, "id": novo.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/dados/{atestado_id}")
async def atualizar_dado(
    atestado_id: int,
    dados: dict,
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório para validação
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualiza um registro"""
    # Valida client_id
    validar_client_id(db, client_id)
    
    # Busca atestado e valida que pertence ao cliente
    atestado = db.query(Atestado).join(Upload).filter(
        Atestado.id == atestado_id,
        Upload.client_id == client_id
    ).first()
    
    if not atestado:
        raise HTTPException(status_code=404, detail="Registro não encontrado ou não pertence ao cliente")
    
    try:
        for key, value in dados.items():
            if hasattr(atestado, key):
                setattr(atestado, key, value)
        
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PRODUTIVIDADE API ====================

@app.get("/api/produtividade")
async def obter_produtividade(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    mes_referencia: Optional[str] = Query(None),  # YYYY-MM
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retorna dados de produtividade do cliente"""
    try:
        # Valida client_id
        validar_client_id(db, client_id)
        
        query = db.query(Produtividade).filter(Produtividade.client_id == client_id)
        
        if mes_referencia:
            query = query.filter(Produtividade.mes_referencia == mes_referencia)
        
        registros = query.order_by(Produtividade.numero_tipo).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": r.id,
                    "numero_tipo": r.numero_tipo,
                    "tipo_consulta": r.tipo_consulta,
                    "ocupacionais": r.ocupacionais or 0,
                    "assistenciais": r.assistenciais or 0,
                    "acidente_trabalho": r.acidente_trabalho or 0,
                    "inss": r.inss or 0,
                    "sinistralidade": r.sinistralidade or 0,
                    "absenteismo": r.absenteismo or 0,
                    "pericia_indireta": r.pericia_indireta or 0,
                    "total": r.total or 0,
                    "mes_referencia": r.mes_referencia
                }
                for r in registros
            ]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar produtividade: {str(e)}")

@app.post("/api/produtividade")
async def salvar_produtividade(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Salva ou atualiza dados de produtividade"""
    try:
        data = await request.json()
        
        client_id = data.get("client_id")
        if not client_id:
            raise HTTPException(status_code=400, detail="client_id é obrigatório")
        
        # Valida client_id
        validar_client_id(db, client_id)
        mes_referencia = data.get("mes_referencia")  # YYYY-MM
        registros = data.get("registros", [])  # Lista de registros
        
        if not mes_referencia:
            raise HTTPException(status_code=400, detail="mes_referencia é obrigatório")
        
        # Remove registros antigos do mesmo mês
        db.query(Produtividade).filter(
            Produtividade.client_id == client_id,
            Produtividade.mes_referencia == mes_referencia
        ).delete()
        
        # Cria novos registros
        novos_registros = []
        for reg in registros:
            # Calcula total
            total = (
                (reg.get("ocupacionais", 0) or 0) +
                (reg.get("assistenciais", 0) or 0) +
                (reg.get("acidente_trabalho", 0) or 0) +
                (reg.get("inss", 0) or 0) +
                (reg.get("sinistralidade", 0) or 0) +
                (reg.get("absenteismo", 0) or 0) +
                (reg.get("pericia_indireta", 0) or 0)
            )
            
            novo = Produtividade(
                client_id=client_id,
                mes_referencia=mes_referencia,
                numero_tipo=str(reg.get("numero_tipo", "")),
                tipo_consulta=reg.get("tipo_consulta", ""),
                ocupacionais=int(reg.get("ocupacionais", 0) or 0),
                assistenciais=int(reg.get("assistenciais", 0) or 0),
                acidente_trabalho=int(reg.get("acidente_trabalho", 0) or 0),
                inss=int(reg.get("inss", 0) or 0),
                sinistralidade=int(reg.get("sinistralidade", 0) or 0),
                absenteismo=int(reg.get("absenteismo", 0) or 0),
                pericia_indireta=int(reg.get("pericia_indireta", 0) or 0),
                total=total
            )
            db.add(novo)
            novos_registros.append(novo)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"{len(novos_registros)} registro(s) salvo(s) com sucesso",
            "count": len(novos_registros)
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar produtividade: {str(e)}")

@app.put("/api/produtividade/{produtividade_id}")
async def atualizar_produtividade(
    produtividade_id: int,
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório para validação
    request: Request = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualiza um registro de produtividade"""
    try:
        # Valida client_id
        validar_client_id(db, client_id)
        
        # Busca registro e valida que pertence ao cliente
        registro = db.query(Produtividade).filter(
            Produtividade.id == produtividade_id,
            Produtividade.client_id == client_id
        ).first()
        if not registro:
            raise HTTPException(status_code=404, detail="Registro não encontrado ou não pertence ao cliente")
        
        data = await request.json()
        
        # Atualiza campos
        registro.numero_tipo = data.get("numero_tipo", registro.numero_tipo)
        registro.tipo_consulta = data.get("tipo_consulta", registro.tipo_consulta)
        registro.ocupacionais = int(data.get("ocupacionais", registro.ocupacionais) or 0)
        registro.assistenciais = int(data.get("assistenciais", registro.assistenciais) or 0)
        registro.acidente_trabalho = int(data.get("acidente_trabalho", registro.acidente_trabalho) or 0)
        registro.inss = int(data.get("inss", registro.inss) or 0)
        registro.sinistralidade = int(data.get("sinistralidade", registro.sinistralidade) or 0)
        registro.absenteismo = int(data.get("absenteismo", registro.absenteismo) or 0)
        registro.pericia_indireta = int(data.get("pericia_indireta", registro.pericia_indireta) or 0)
        
        # Recalcula total
        registro.total = (
            registro.ocupacionais +
            registro.assistenciais +
            registro.acidente_trabalho +
            registro.inss +
            registro.sinistralidade +
            registro.absenteismo +
            registro.pericia_indireta
        )
        
        db.commit()
        
        return {
            "success": True,
            "message": "Registro atualizado com sucesso",
            "data": {
                "id": registro.id,
                "numero_tipo": registro.numero_tipo,
                "tipo_consulta": registro.tipo_consulta,
                "ocupacionais": registro.ocupacionais,
                "assistenciais": registro.assistenciais,
                "acidente_trabalho": registro.acidente_trabalho,
                "inss": registro.inss,
                "sinistralidade": registro.sinistralidade,
                "absenteismo": registro.absenteismo,
                "pericia_indireta": registro.pericia_indireta,
                "total": registro.total,
                "mes_referencia": registro.mes_referencia
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar: {str(e)}")

@app.delete("/api/produtividade/{produtividade_id}")
async def excluir_produtividade(
    produtividade_id: int,
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório para validação
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Exclui um registro de produtividade"""
    try:
        # Valida client_id
        validar_client_id(db, client_id)
        
        # Busca registro e valida que pertence ao cliente
        registro = db.query(Produtividade).filter(
            Produtividade.id == produtividade_id,
            Produtividade.client_id == client_id
        ).first()
        if not registro:
            raise HTTPException(status_code=404, detail="Registro não encontrado ou não pertence ao cliente")
        
        db.delete(registro)
        db.commit()
        
        return {"success": True, "message": "Registro excluído com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir: {str(e)}")

@app.get("/api/produtividade/evolucao")
async def obter_evolucao_produtividade(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    agrupar_por: str = Query("mes", description="Agrupar por 'mes' ou 'ano'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retorna dados agregados de produtividade para gráficos de evolução"""
    try:
        # Valida client_id
        validar_client_id(db, client_id)
        
        # Busca todos os registros do cliente
        registros = db.query(Produtividade).filter(
            Produtividade.client_id == client_id
        ).order_by(Produtividade.mes_referencia).all()
        
        if not registros:
            return {
                "success": True,
                "data": [],
                "agrupar_por": agrupar_por
            }
        
        # Agrupa por mês ou ano
        # Primeiro agrupa por mês e tipo_consulta
        dados_por_mes_tipo = {}
        
        for reg in registros:
            mes_ref = reg.mes_referencia  # YYYY-MM
            tipo = reg.tipo_consulta or "sem-tipo"
            
            if agrupar_por == "ano":
                # Agrupa por ano (YYYY)
                chave = mes_ref.split('-')[0] if mes_ref else "sem-ano"
            else:
                # Agrupa por mês (YYYY-MM)
                chave = mes_ref if mes_ref else "sem-mes"
            
            chave_completa = f"{chave}_{tipo}"
            
            if chave_completa not in dados_por_mes_tipo:
                dados_por_mes_tipo[chave_completa] = {
                    "periodo": chave,
                    "tipo_consulta": tipo,
                    "ocupacionais": 0,
                    "assistenciais": 0,
                    "acidente_trabalho": 0,
                    "inss": 0,
                    "sinistralidade": 0,
                    "absenteismo": 0,
                    "pericia_indireta": 0,
                    "total": 0
                }
            
            # Soma os valores
            dados_por_mes_tipo[chave_completa]["ocupacionais"] += reg.ocupacionais or 0
            dados_por_mes_tipo[chave_completa]["assistenciais"] += reg.assistenciais or 0
            dados_por_mes_tipo[chave_completa]["acidente_trabalho"] += reg.acidente_trabalho or 0
            dados_por_mes_tipo[chave_completa]["inss"] += reg.inss or 0
            dados_por_mes_tipo[chave_completa]["sinistralidade"] += reg.sinistralidade or 0
            dados_por_mes_tipo[chave_completa]["absenteismo"] += reg.absenteismo or 0
            dados_por_mes_tipo[chave_completa]["pericia_indireta"] += reg.pericia_indireta or 0
            dados_por_mes_tipo[chave_completa]["total"] += reg.total or 0
        
        # Agora agrega apenas os registros do tipo "Agendados"
        dados_agregados = {}
        
        for chave_completa, dados in dados_por_mes_tipo.items():
            if dados["tipo_consulta"] == "Agendados":
                periodo = dados["periodo"]
                
                if periodo not in dados_agregados:
                    dados_agregados[periodo] = {
                        "periodo": periodo,
                        "ocupacionais": 0,
                        "assistenciais": 0,
                        "acidente_trabalho": 0,
                        "inss": 0,
                        "sinistralidade": 0,
                        "absenteismo": 0,
                        "pericia_indireta": 0,
                        "total": 0
                    }
                
                # Soma apenas os valores de "Agendados"
                dados_agregados[periodo]["ocupacionais"] += dados["ocupacionais"]
                dados_agregados[periodo]["assistenciais"] += dados["assistenciais"]
                dados_agregados[periodo]["acidente_trabalho"] += dados["acidente_trabalho"]
                dados_agregados[periodo]["inss"] += dados["inss"]
                dados_agregados[periodo]["sinistralidade"] += dados["sinistralidade"]
                dados_agregados[periodo]["absenteismo"] += dados["absenteismo"]
                dados_agregados[periodo]["pericia_indireta"] += dados["pericia_indireta"]
                dados_agregados[periodo]["total"] += dados["total"]
        
        # Converte para lista ordenada
        lista_ordenada = sorted(
            dados_agregados.values(),
            key=lambda x: x["periodo"]
        )
        
        return {
            "success": True,
            "data": lista_ordenada,
            "agrupar_por": agrupar_por
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar evolução: {str(e)}")

@app.delete("/api/dados/{atestado_id}")
async def excluir_dado(
    atestado_id: int,
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório para validação
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Exclui um registro"""
    # Valida client_id
    validar_client_id(db, client_id)
    
    # Busca atestado e valida que pertence ao cliente
    atestado = db.query(Atestado).join(Upload).filter(
        Atestado.id == atestado_id,
        Upload.client_id == client_id
    ).first()
    
    if not atestado:
        raise HTTPException(status_code=404, detail="Registro não encontrado ou não pertence ao cliente")
    
    try:
        db.delete(atestado)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/funcionario/atualizar")
async def atualizar_funcionario(
    nome: str = Query(...),
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    genero: Optional[str] = Query(None),
    setor: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualiza todos os registros de um funcionário (em massa)"""
    try:
        # Valida client_id
        validar_client_id(db, client_id)
        
        # Busca todos os atestados do funcionário
        atestados = db.query(Atestado).join(Upload).filter(
            Upload.client_id == client_id,
            (Atestado.nomecompleto == nome) | (Atestado.nome_funcionario == nome)
        ).all()
        
        if not atestados:
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")
        
        atualizados = 0
        for atestado in atestados:
            if genero is not None:
                atestado.genero = genero.upper()[:1] if genero else None
            if setor is not None:
                atestado.setor = setor
        
        db.commit()
        return {
            "success": True,
            "total_atualizados": len(atestados),
            "mensagem": f"{len(atestados)} registro(s) atualizado(s) com sucesso"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar funcionário: {str(e)}")

@app.put("/api/funcionarios/atualizar-massa")
async def atualizar_funcionarios_massa(
    nomes: List[str] = Query(...),
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),  # Obrigatório
    genero: Optional[str] = Query(None),
    setor: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualiza múltiplos funcionários em massa"""
    try:
        # Valida client_id
        validar_client_id(db, client_id)
        
        if not nomes or len(nomes) == 0:
            raise HTTPException(status_code=400, detail="Nenhum funcionário selecionado")
        
        total_registros_atualizados = 0
        funcionarios_atualizados = 0
        
        for nome in nomes:
            # Busca todos os atestados do funcionário
            atestados = db.query(Atestado).join(Upload).filter(
                Upload.client_id == client_id,
                (Atestado.nomecompleto == nome) | (Atestado.nome_funcionario == nome)
            ).all()
            
            if atestados:
                funcionarios_atualizados += 1
                for atestado in atestados:
                    if genero is not None:
                        atestado.genero = genero.upper()[:1] if genero else None
                    if setor is not None:
                        atestado.setor = setor
                    total_registros_atualizados += 1
        
        db.commit()
        return {
            "success": True,
            "funcionarios_atualizados": funcionarios_atualizados,
            "total_registros_atualizados": total_registros_atualizados,
            "mensagem": f"{funcionarios_atualizados} funcionário(s) atualizado(s) com sucesso ({total_registros_atualizados} registro(s))"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar funcionários: {str(e)}")

# ==================== ROUTES - UPLOAD INTELIGENTE ====================

@app.post("/api/upload/analyze")
async def analyze_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Analisa arquivo e sugere configurações das colunas"""
    try:
        # Salva arquivo temporário
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"temp_{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOADS_DIR, filename)
        
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Analisa arquivo
        processor = ExcelProcessor(file_path)
        df = processor.df
        
        # Analisa cada coluna
        columns = []
        for col in df.columns:
            column_info = analyze_column(col, df[col])
            columns.append(column_info)
        
        # Remove arquivo temporário
        os.remove(file_path)
        
        return {"columns": columns}
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/upload/process")
async def process_file_with_config(
    file: UploadFile = File(...),
    config: str = Form(...),
    client_id: int = Form(...),  # Obrigatório, sem valor padrão
    db: Session = Depends(get_db)
):
    """Processa arquivo com configurações das colunas"""
    try:
        # Valida client_id
        validar_client_id(db, client_id)
        
        # Parse configurações
        column_configs = json.loads(config)
        
        # Salva arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOADS_DIR, filename)
        
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Processa com configurações
        processor = ExcelProcessor(file_path)
        registros = processor.processar()
        
        if not registros:
            raise HTTPException(status_code=400, detail="Erro ao processar planilha")
        
        # Detecta mês de referência
        mes_ref = None
        if registros:
            primeiro_registro = registros[0]
            if 'data_afastamento' in primeiro_registro and primeiro_registro['data_afastamento']:
                mes_ref = primeiro_registro['data_afastamento'].strftime('%Y-%m')
        
        # Cria upload
        upload = Upload(
            client_id=client_id,
            filename=filename,
            mes_referencia=mes_ref,
            total_registros=len(registros),
            data_upload=datetime.now()
        )
        db.add(upload)
        db.commit()
        db.refresh(upload)
        
        # Salva registros
        for dados in registros:
            atestado = Atestado(
                upload_id=upload.id,
                **dados
            )
            db.add(atestado)
        
        db.commit()
        
        return {
            "success": True,
            "upload_id": upload.id,
            "total_records": len(registros),
            "message": "Dados processados com sucesso!"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

def analyze_column(column_name: str, column_data):
    """Analisa uma coluna e sugere configurações"""
    import pandas as pd
    import re
    
    # Amostra dos dados
    sample_data = column_data.dropna().head(5).tolist()
    preview = ', '.join([str(x)[:20] for x in sample_data[:3]])
    
    # Detecta tipo de dados
    data_type = str(column_data.dtype)
    
    # Sugere tipo baseado no nome da coluna
    column_lower = column_name.lower()
    suggested_type = 'outro'
    analysis_important = True
    ai_notes = []
    
    # Detecção inteligente por nome
    if any(word in column_lower for word in ['nome', 'funcionario', 'funcionário']):
        suggested_type = 'nome_funcionario'
        ai_notes.append("Detectado como nome de funcionário")
    elif any(word in column_lower for word in ['cpf', 'documento']):
        suggested_type = 'cpf'
        ai_notes.append("Detectado como CPF")
    elif any(word in column_lower for word in ['matricula', 'matrícula', 'codigo', 'código']):
        suggested_type = 'matricula'
        ai_notes.append("Detectado como matrícula")
    elif any(word in column_lower for word in ['setor', 'departamento', 'area', 'área']):
        suggested_type = 'setor'
        ai_notes.append("Detectado como setor")
    elif any(word in column_lower for word in ['cargo', 'funcao', 'função']):
        suggested_type = 'cargo'
        ai_notes.append("Detectado como cargo")
    elif any(word in column_lower for word in ['afastamento', 'inicio', 'início']):
        suggested_type = 'data_afastamento'
        ai_notes.append("Detectado como data de afastamento")
    elif any(word in column_lower for word in ['retorno', 'fim', 'termino', 'término']):
        suggested_type = 'data_retorno'
        ai_notes.append("Detectado como data de retorno")
    elif any(word in column_lower for word in ['cid', 'codigo', 'código']):
        suggested_type = 'cid'
        ai_notes.append("Detectado como CID")
    elif any(word in column_lower for word in ['descricao', 'descrição', 'diagnostico', 'diagnóstico']):
        suggested_type = 'descricao_cid'
        ai_notes.append("Detectado como descrição do CID")
    elif any(word in column_lower for word in ['dias', 'dia']):
        suggested_type = 'dias_atestado'
        ai_notes.append("Detectado como dias de atestado")
    elif any(word in column_lower for word in ['horas', 'hora']):
        suggested_type = 'horas_atestado'
        ai_notes.append("Detectado como horas de atestado")
    
    # Análise do conteúdo
    if data_type in ['datetime64[ns]', 'object'] and column_data.dropna().empty == False:
        try:
            pd.to_datetime(column_data.dropna().iloc[0])
            if suggested_type == 'outro':
                suggested_type = 'data_afastamento'
                ai_notes.append("Detectado como data pelo conteúdo")
        except:
            pass
    
    # Verifica se é numérico
    if data_type in ['int64', 'float64']:
        if suggested_type == 'outro':
            if column_data.max() < 100:
                suggested_type = 'dias_atestado'
                ai_notes.append("Detectado como dias (valor numérico baixo)")
            else:
                suggested_type = 'horas_atestado'
                ai_notes.append("Detectado como horas (valor numérico alto)")
    
    # Determina se é importante para análise
    if suggested_type == 'outro':
        analysis_important = False
        ai_notes.append("Coluna não identificada - considere excluir")
    
    return {
        "name": column_name,
        "preview": preview,
        "suggested_type": suggested_type,
        "analysis_important": analysis_important,
        "include": analysis_important,
        "ai_notes": "; ".join(ai_notes) if ai_notes else "Coluna analisada automaticamente"
    }

# ==================== SAVED FILTERS API ====================

@app.get("/api/filtros-salvos")
async def listar_filtros_salvos(
    client_id: int = Query(..., description="ID do cliente"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Lista filtros salvos do usuário para um cliente"""
    try:
        filtros = db.query(SavedFilter).filter(
            SavedFilter.user_id == current_user.id,
            SavedFilter.client_id == client_id
        ).order_by(SavedFilter.updated_at.desc()).all()
        
        return [
            {
                "id": f.id,
                "nome": f.nome,
                "mes_inicio": f.mes_inicio,
                "mes_fim": f.mes_fim,
                "funcionarios": json.loads(f.funcionarios) if f.funcionarios else [],
                "setores": json.loads(f.setores) if f.setores else [],
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "updated_at": f.updated_at.isoformat() if f.updated_at else None
            }
            for f in filtros
        ]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao listar filtros salvos: {str(e)}")

@app.post("/api/filtros-salvos")
async def salvar_filtro(
    client_id: int = Form(...),
    nome: str = Form(...),
    mes_inicio: Optional[str] = Form(None),
    mes_fim: Optional[str] = Form(None),
    funcionarios: Optional[str] = Form(None),  # JSON string array
    setores: Optional[str] = Form(None),  # JSON string array
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Salva um novo filtro"""
    try:
        # Valida client_id
        validar_client_id(db, client_id)
        
        # Valida nome
        if not nome or len(nome.strip()) == 0:
            raise HTTPException(status_code=400, detail="Nome do filtro é obrigatório")
        
        # Valida JSON de funcionários e setores
        funcionarios_list = []
        setores_list = []
        
        if funcionarios:
            try:
                funcionarios_list = json.loads(funcionarios)
                if not isinstance(funcionarios_list, list):
                    funcionarios_list = []
            except:
                funcionarios_list = []
        
        if setores:
            try:
                setores_list = json.loads(setores)
                if not isinstance(setores_list, list):
                    setores_list = []
            except:
                setores_list = []
        
        # Cria filtro salvo
        filtro = SavedFilter(
            user_id=current_user.id,
            client_id=client_id,
            nome=nome.strip(),
            mes_inicio=mes_inicio.strip() if mes_inicio else None,
            mes_fim=mes_fim.strip() if mes_fim else None,
            funcionarios=json.dumps(funcionarios_list) if funcionarios_list else None,
            setores=json.dumps(setores_list) if setores_list else None
        )
        
        db.add(filtro)
        db.commit()
        db.refresh(filtro)
        
        return {
            "id": filtro.id,
            "nome": filtro.nome,
            "mes_inicio": filtro.mes_inicio,
            "mes_fim": filtro.mes_fim,
            "funcionarios": funcionarios_list,
            "setores": setores_list,
            "message": "Filtro salvo com sucesso"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar filtro: {str(e)}")

@app.put("/api/filtros-salvos/{filtro_id}")
async def atualizar_filtro(
    filtro_id: int,
    nome: Optional[str] = Form(None),
    mes_inicio: Optional[str] = Form(None),
    mes_fim: Optional[str] = Form(None),
    funcionarios: Optional[str] = Form(None),
    setores: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Atualiza um filtro salvo"""
    try:
        filtro = db.query(SavedFilter).filter(
            SavedFilter.id == filtro_id,
            SavedFilter.user_id == current_user.id
        ).first()
        
        if not filtro:
            raise HTTPException(status_code=404, detail="Filtro não encontrado")
        
        if nome:
            filtro.nome = nome.strip()
        if mes_inicio is not None:
            filtro.mes_inicio = mes_inicio.strip() if mes_inicio else None
        if mes_fim is not None:
            filtro.mes_fim = mes_fim.strip() if mes_fim else None
        
        if funcionarios is not None:
            try:
                funcionarios_list = json.loads(funcionarios) if funcionarios else []
                filtro.funcionarios = json.dumps(funcionarios_list) if funcionarios_list else None
            except:
                pass
        
        if setores is not None:
            try:
                setores_list = json.loads(setores) if setores else []
                filtro.setores = json.dumps(setores_list) if setores_list else None
            except:
                pass
        
        filtro.updated_at = datetime.now()
        db.commit()
        
        return {
            "id": filtro.id,
            "nome": filtro.nome,
            "message": "Filtro atualizado com sucesso"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar filtro: {str(e)}")

@app.delete("/api/filtros-salvos/{filtro_id}")
async def deletar_filtro(
    filtro_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deleta um filtro salvo"""
    try:
        filtro = db.query(SavedFilter).filter(
            SavedFilter.id == filtro_id,
            SavedFilter.user_id == current_user.id
        ).first()
        
        if not filtro:
            raise HTTPException(status_code=404, detail="Filtro não encontrado")
        
        db.delete(filtro)
        db.commit()
        
        return {"message": "Filtro deletado com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar filtro: {str(e)}")

@app.get("/api/filtros-salvos/{filtro_id}/aplicar")
async def aplicar_filtro_salvo(
    filtro_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retorna os parâmetros de um filtro salvo para aplicação"""
    try:
        filtro = db.query(SavedFilter).filter(
            SavedFilter.id == filtro_id,
            SavedFilter.user_id == current_user.id
        ).first()
        
        if not filtro:
            raise HTTPException(status_code=404, detail="Filtro não encontrado")
        
        return {
            "mes_inicio": filtro.mes_inicio,
            "mes_fim": filtro.mes_fim,
            "funcionarios": json.loads(filtro.funcionarios) if filtro.funcionarios else [],
            "setores": json.loads(filtro.setores) if filtro.setores else []
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao obter filtro: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
