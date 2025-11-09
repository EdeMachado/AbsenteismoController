"""
FastAPI Main Application - AbsenteismoController v2.0
"""
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query, Form
from typing import List
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, nullslast
from typing import Optional, List
import os
import shutil
import json
from datetime import datetime
import uuid
from collections import OrderedDict
import pandas as pd

from .database import get_db, init_db, run_migrations
from .models import Client, Upload, Atestado, User, Config
from .excel_processor import ExcelProcessor
from .analytics import Analytics
from .insights import InsightsEngine
from .report_generator import ReportGenerator
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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para garantir UTF-8
@app.middleware("http")
async def add_charset_header(request, call_next):
    response = await call_next(request)
    response.headers["Content-Type"] = response.headers.get("Content-Type", "application/json") + "; charset=utf-8"
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

# Initialize database
@app.on_event("startup")
async def startup_event():
    init_db()
    run_migrations()
    os.makedirs(LOGOS_DIR, exist_ok=True)
    # Cria cliente padrão se não existir
    db = next(get_db())
    client = db.query(Client).filter(Client.id == 1).first()
    if not client:
        client = Client(id=1, nome="GrupoBiomed", cnpj="00.000.000/0001-00")
        db.add(client)
        db.commit()
    # Cria usuário admin padrão se não existir
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
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
    # Configurações padrão
    if not db.query(Config).filter(Config.chave == "nome_sistema").first():
        set_config_value(db, "nome_sistema", "AbsenteismoController", "Nome do sistema", "string")
        set_config_value(db, "empresa", "GrupoBiomed", "Nome da empresa", "string")
        set_config_value(db, "email_contato", "contato@grupobiomed.com", "Email de contato", "string")
        set_config_value(db, "tema_escuro", "false", "Tema escuro ativado", "boolean")
        set_config_value(db, "itens_por_pagina", "50", "Itens por página", "number")
    db.close()

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
async def configuracoes_page(current_user: User = Depends(get_current_active_user)):
    """Página de configurações"""
    file_path = os.path.join(FRONTEND_DIR, "configuracoes.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/", response_class=HTMLResponse)
async def index():
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

@app.get("/relatorios", response_class=HTMLResponse)
async def relatorios_page():
    """Página de relatórios"""
    file_path = os.path.join(FRONTEND_DIR, "relatorios.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

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
async def comparativos_page(current_user: User = Depends(get_current_active_user)):
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
async def health_check():
    """Health check"""
    return {"status": "ok", "version": "2.0.0"}

# ==================== AUTHENTICATION API ====================

@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login de usuário"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
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
async def get_config(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
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
async def get_config_value_api(chave: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
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

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    client_id: int = Form(1),
    db: Session = Depends(get_db)
):
    """Upload de planilha"""
    try:
        # Salva arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOADS_DIR, saved_filename)
        
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Processa Excel
        processor = ExcelProcessor(file_path)
        registros = processor.processar()
        
        if not registros:
            raise HTTPException(status_code=400, detail="Erro ao processar planilha")
        
        # Detecta mês de referência (pega do primeiro registro)
        mes_ref = None
        if registros and registros[0].get('data_afastamento'):
            data = registros[0]['data_afastamento']
            if isinstance(data, datetime):
                mes_ref = data.strftime("%Y-%m")
            else:
                mes_ref = datetime.now().strftime("%Y-%m")
        else:
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
        
        # Salva atestados
        for reg in registros:
            atestado = Atestado(
                upload_id=upload.id,
                **reg
            )
            db.add(atestado)
        
        db.commit()
        
        return {
            "success": True,
            "upload_id": upload.id,
            "total_registros": len(registros),
            "mes_referencia": mes_ref
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/uploads")
async def list_uploads(
    client_id: int = 1,
    db: Session = Depends(get_db)
):
    """Lista uploads"""
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
    client_id: int = 1,
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    funcionario: Optional[List[str]] = Query(None),
    setor: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """Dashboard principal"""
    try:
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
            evolucao_setor = analytics.evolucao_por_setor(client_id, 12, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular evolução por setor: {e}")
            evolucao_setor = {}
        
        try:
            comparativo_dias_horas = analytics.comparativo_dias_horas(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular comparativo dias/horas: {e}")
            comparativo_dias_horas = []
        
        try:
            frequencia_atestados = analytics.frequencia_atestados_por_funcionario(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular frequência de atestados: {e}")
            frequencia_atestados = []
        
        try:
            dias_setor_genero = analytics.dias_perdidos_setor_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
        except Exception as e:
            print(f"Erro ao calcular dias por setor e gênero: {e}")
            dias_setor_genero = []
        
        try:
            insights = insights_engine.gerar_insights(client_id)
        except Exception as e:
            print(f"Erro ao gerar insights: {e}")
            insights = []
        
        # Busca alertas
        try:
            alertas_system = AlertasSystem(db)
            alertas = alertas_system.detectar_alertas(client_id, mes_inicio, mes_fim)
        except Exception as e:
            print(f"Erro ao detectar alertas: {e}")
            alertas = []
        
        resultado = {
            "metricas": metricas,
            "top_cids": top_cids,
            "top_setores": top_setores,
            "evolucao_mensal": evolucao,
            "distribuicao_genero": distribuicao_genero,
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
            "insights": insights,
            "alertas": alertas
        }
        
        # Corrige encoding antes de retornar
        return corrigir_encoding_json(resultado)
        
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao carregar dashboard: {error_detail}")

@app.get("/api/filtros")
async def obter_filtros(
    client_id: int = 1,
    db: Session = Depends(get_db)
):
    """Retorna lista de funcionários e setores para preencher os filtros"""
    try:
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

@app.get("/api/alertas")
async def obter_alertas(
    client_id: int = 1,
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retorna alertas automáticos do sistema"""
    try:
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
async def listar_clientes(db: Session = Depends(get_db)):
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
async def obter_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Obtém um cliente específico"""
    try:
        cliente = db.query(Client).filter(Client.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
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
            "logo_url": cliente.logo_url,
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
    db: Session = Depends(get_db)
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
async def criar_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
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
async def atualizar_cliente(cliente_id: int, cliente: ClienteCreate, db: Session = Depends(get_db)):
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
        
        # Atualiza campos
        logo_url_novo = cliente.logo_url
        if logo_url_novo is not None:
            logo_url_novo = logo_url_novo.strip()
            if not logo_url_novo:
                if cliente_db.logo_url:
                    remover_logo_arquivo(cliente_db.logo_url)
                cliente_db.logo_url = None
            else:
                cliente_db.logo_url = logo_url_novo

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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Realiza upload/atualização do logo de um cliente."""
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

        if cliente.logo_url and cliente.logo_url != novo_logo_url:
            remover_logo_arquivo(cliente.logo_url)

        cliente.logo_url = novo_logo_url
        cliente.updated_at = datetime.now()
        db.commit()
        db.refresh(cliente)

        return {
            "logo_url": cliente.logo_url,
            "message": "Logo atualizado com sucesso"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao enviar logo: {str(e)}")

@app.delete("/api/clientes/{cliente_id}")
async def deletar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Deleta um cliente"""
    try:
        cliente = db.query(Client).filter(Client.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Verifica se tem uploads
        if len(cliente.uploads) > 0:
            raise HTTPException(status_code=400, detail="Cliente possui dados. Utilize o arquivo morto.")
        
        db.delete(cliente)
        db.commit()
        
        return {"message": "Cliente deletado com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar cliente: {str(e)}")

@app.post("/api/clientes/{cliente_id}/arquivar")
async def arquivar_cliente(cliente_id: int, db: Session = Depends(get_db)):
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

@app.post("/api/clientes/{cliente_id}/ativar")
async def ativar_cliente(cliente_id: int, db: Session = Depends(get_db)):
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
    client_id: int = 1,
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    funcionario: Optional[List[str]] = Query(None),
    setor: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """Retorna todos os dados necessários para a apresentação com análises IA"""
    try:
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
        
        # Gera análises IA para cada gráfico
        slides = []
        
        # Slide 0: Título/Capa
        slides.append({
            "id": 0,
            "tipo": "capa",
            "titulo": "Capa",
            "subtitulo": "",
            "dados": None,
            "analise": None
        })
        
        # Slide 1: KPIs
        if metricas:
            slides.append({
                "id": 1,
                "tipo": "kpis",
                "titulo": "Indicadores Principais",
                "subtitulo": "Visão geral do absenteísmo",
                "dados": metricas,
                "analise": insights_engine.gerar_analise_grafico('kpis', None, metricas)
            })
        
        # Slide 2: Dias Perdidos por Funcionário
        if top_funcionarios:
            slides.append({
                "id": 2,
                "tipo": "funcionarios_dias",
                "titulo": "Dias Perdidos por Funcionário",
                "subtitulo": "TOP 10 funcionários com maior índice",
                "dados": top_funcionarios,
                "analise": insights_engine.gerar_analise_grafico('funcionarios_dias', top_funcionarios, metricas)
            })
        
        # Slide 3: TOP 10 CIDs
        if top_cids:
            slides.append({
                "id": 3,
                "tipo": "top_cids",
                "titulo": "TOP 10 Doenças mais Frequentes",
                "subtitulo": "Principais causas de afastamento",
                "dados": top_cids,
                "analise": insights_engine.gerar_analise_grafico('top_cids', top_cids, metricas)
            })
        
        # Slide 4: Evolução Mensal
        if evolucao:
            slides.append({
                "id": 4,
                "tipo": "evolucao_mensal",
                "titulo": "Evolução Mensal",
                "subtitulo": "Últimos 12 meses",
                "dados": evolucao,
                "analise": insights_engine.gerar_analise_grafico('evolucao_mensal', evolucao, metricas)
            })
        
        # Slide 5: TOP 5 Setores
        if top_setores:
            slides.append({
                "id": 5,
                "tipo": "top_setores",
                "titulo": "TOP 5 Setores",
                "subtitulo": "Setores com mais atestados",
                "dados": top_setores,
                "analise": insights_engine.gerar_analise_grafico('top_setores', top_setores, metricas)
            })
        
        # Slide 6: Por Gênero
        if distribuicao_genero:
            slides.append({
                "id": 6,
                "tipo": "genero",
                "titulo": "Distribuição por Gênero",
                "subtitulo": "Masculino vs Feminino",
                "dados": distribuicao_genero,
                "analise": insights_engine.gerar_analise_grafico('genero', distribuicao_genero, metricas)
            })
        
        # Slide 7: Dias por Doença
        if top_cids_dias:
            slides.append({
                "id": 7,
                "tipo": "dias_doenca",
                "titulo": "Dias por Doença",
                "subtitulo": "Total de dias perdidos",
                "dados": top_cids_dias,
                "analise": insights_engine.gerar_analise_grafico('dias_doenca', top_cids_dias, metricas)
            })
        
        # Slide 8: Escalas
        if top_escalas:
            slides.append({
                "id": 8,
                "tipo": "escalas",
                "titulo": "Escalas com mais Atestados",
                "subtitulo": "TOP 10 escalas com maior incidência",
                "dados": top_escalas,
                "analise": insights_engine.gerar_analise_grafico('escalas', top_escalas, metricas)
            })
        
        # Slide 9: Motivos
        if top_motivos:
            slides.append({
                "id": 9,
                "tipo": "motivos",
                "titulo": "Motivos de Incidência",
                "subtitulo": "Distribuição percentual dos motivos",
                "dados": top_motivos,
                "analise": insights_engine.gerar_analise_grafico('motivos', top_motivos, metricas)
            })
        
        # Slide 10: Centro de Custo
        if dias_centro_custo:
            slides.append({
                "id": 10,
                "tipo": "centro_custo",
                "titulo": "Dias Perdidos por Centro de Custo",
                "subtitulo": "TOP 10 setores",
                "dados": dias_centro_custo,
                "analise": insights_engine.gerar_analise_grafico('centro_custo', dias_centro_custo, metricas)
            })
        
        # Slide 11: Distribuição de Dias
        if distribuicao_dias:
            slides.append({
                "id": 11,
                "tipo": "distribuicao_dias",
                "titulo": "Distribuição de Dias por Atestado",
                "subtitulo": "Histograma de frequência",
                "dados": distribuicao_dias,
                "analise": insights_engine.gerar_analise_grafico('distribuicao_dias', distribuicao_dias, metricas)
            })
        
        # Slide 12: Média por CID
        if media_cid:
            slides.append({
                "id": 12,
                "tipo": "media_cid",
                "titulo": "Média de Dias por CID",
                "subtitulo": "Doenças com maior média de dias",
                "dados": media_cid,
                "analise": insights_engine.gerar_analise_grafico('media_cid', media_cid, metricas)
            })
        
        # Slide 13: Setor e Gênero
        if dias_setor_genero:
            slides.append({
                "id": 13,
                "tipo": "setor_genero",
                "titulo": "Dias Perdidos por Setor e Gênero",
                "subtitulo": "Comparativo entre gêneros por setor",
                "dados": dias_setor_genero,
                "analise": insights_engine.gerar_analise_grafico('setor_genero', dias_setor_genero, metricas)
            })
        
        # Slide 14: Ações - Introdução
        slides.append({
            "id": 14,
            "tipo": "acoes_intro",
            "titulo": "Ações",
            "subtitulo": "Intervenções junto aos colaboradores",
            "dados": None,
            "analise": None
        })
        
        # Slide 15: Ações - Saúde Física
        slides.append({
            "id": 15,
            "tipo": "acoes_saude_fisica",
            "titulo": "Ações – Saúde Física",
            "subtitulo": "Promoção da saúde preventiva",
            "dados": None,
            "analise": None
        })
        
        # Slide 16: Ações - Saúde Emocional
        slides.append({
            "id": 16,
            "tipo": "acoes_saude_emocional",
            "titulo": "Ações – Saúde Emocional",
            "subtitulo": "Bem-estar psicológico e emocional",
            "dados": None,
            "analise": None
        })
        
        # Slide 17: Ações - Saúde Social
        slides.append({
            "id": 17,
            "tipo": "acoes_saude_social",
            "titulo": "Ações – Saúde Social",
            "subtitulo": "Integração e relacionamento interpessoal",
            "dados": None,
            "analise": None
        })
        
        return {
            "slides": slides,
            "total_slides": len(slides)
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar apresentação: {str(e)}")

@app.get("/api/preview/{upload_id}")
async def preview_data(
    upload_id: int,
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db)
):
    """Preview dos dados do upload"""
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
    client_id: int = 1,
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Análise por funcionários"""
    analytics = Analytics(db)
    return analytics.top_funcionarios(client_id, 1000, mes_inicio, mes_fim)

@app.get("/api/analises/setores")
async def analise_setores(
    client_id: int = 1,
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Análise por setores"""
    analytics = Analytics(db)
    return analytics.top_setores(client_id, 20, mes_inicio, mes_fim)

@app.get("/api/analises/cids")
async def analise_cids(
    client_id: int = 1,
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Análise por CIDs"""
    analytics = Analytics(db)
    return analytics.top_cids(client_id, 20, mes_inicio, mes_fim)

@app.get("/api/tendencias")
async def tendencias(
    client_id: int = 1,
    db: Session = Depends(get_db)
):
    """Análise de tendências"""
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

@app.get("/api/relatorios/comparativo")
async def relatorio_comparativo(
    client_id: int = 1,
    periodo1_inicio: str = Query(...),
    periodo1_fim: str = Query(...),
    periodo2_inicio: str = Query(...),
    periodo2_fim: str = Query(...),
    db: Session = Depends(get_db)
):
    """Relatório comparativo entre períodos"""
    analytics = Analytics(db)
    return analytics.comparativo_periodos(
        client_id,
        (periodo1_inicio, periodo1_fim),
        (periodo2_inicio, periodo2_fim)
    )

@app.delete("/api/uploads/{upload_id}")
async def delete_upload(
    upload_id: int,
    db: Session = Depends(get_db)
):
    """Deleta um upload e seus dados"""
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload não encontrado")
    
    db.delete(upload)
    db.commit()
    
    return {"success": True, "message": "Upload deletado com sucesso"}

@app.get("/api/export/excel")
async def export_excel(
    client_id: int = 1,
    mes: Optional[str] = None,
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    upload_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Exporta relatório completo para Excel"""
    try:
        analytics = Analytics(db)
        report_gen = ReportGenerator()
        
        # Busca todos os dados (igual ao PDF)
        metricas_gerais = analytics.metricas_gerais(client_id, mes_inicio, mes_fim, None, None)
        top_cids = analytics.top_cids(client_id, 10, mes_inicio, mes_fim, None, None)
        top_funcionarios = analytics.top_funcionarios(client_id, 10, mes_inicio, mes_fim, None, None)
        top_setores = analytics.top_setores(client_id, 10, mes_inicio, mes_fim, None, None)
        
        # Busca outros dados
        evolucao_mensal = []
        try:
            evolucao_mensal = analytics.evolucao_mensal(client_id, 12, mes_inicio, mes_fim, None, None)
        except:
            pass
        
        distribuicao_genero = []
        try:
            distribuicao_genero = analytics.distribuicao_genero(client_id, mes_inicio, mes_fim, None, None)
        except:
            pass
        
        top_escalas = []
        try:
            top_escalas = analytics.top_escalas(client_id, 10, mes_inicio, mes_fim, None, None)
        except:
            pass
        
        top_motivos = []
        try:
            top_motivos = analytics.top_motivos(client_id, 10, mes_inicio, mes_fim, None, None)
        except:
            pass
        
        dias_centro_custo = []
        try:
            dias_centro_custo = analytics.dias_perdidos_por_centro_custo(client_id, 10, mes_inicio, mes_fim, None, None)
        except:
            pass
        
        distribuicao_dias = []
        try:
            distribuicao_dias = analytics.distribuicao_dias_por_atestado(client_id, mes_inicio, mes_fim, None, None)
        except:
            pass
        
        media_cid = []
        try:
            media_cid = analytics.media_dias_por_cid(client_id, 10, mes_inicio, mes_fim, None, None)
        except:
            pass
        
        top_cids_dias = []
        try:
            top_cids_dias = analytics.top_cids(client_id, 5, mes_inicio, mes_fim, None, None)
        except:
            pass
        
        dias_setor_genero = []
        try:
            dias_setor_genero = analytics.dias_perdidos_setor_genero(client_id, mes_inicio, mes_fim, None, None)
        except:
            pass
        
        # Busca dados completos
        query = db.query(Atestado).join(Upload).filter(Upload.client_id == client_id)
        if upload_id:
            query = query.filter(Upload.id == upload_id)
        elif mes:
            query = query.filter(Upload.mes_referencia == mes)
        elif mes_inicio and mes_fim:
            query = query.filter(Upload.mes_referencia >= mes_inicio, Upload.mes_referencia <= mes_fim)
        
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
        
        # Preparar dados para relatório
        dados_relatorio = {
            'top_cids': top_cids,
            'top_funcionarios': top_funcionarios,
            'top_setores': top_setores,
            'evolucao_mensal': evolucao_mensal,
            'distribuicao_genero': distribuicao_genero,
            'top_escalas': top_escalas,
            'top_motivos': top_motivos,
            'dias_centro_custo': dias_centro_custo,
            'distribuicao_dias': distribuicao_dias,
            'media_cid': media_cid,
            'top_cids_dias': top_cids_dias,
            'dias_setor_genero': dias_setor_genero
        }
        
        # Gerar arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_absenteismo_{timestamp}.xlsx"
        filepath = os.path.join(EXPORTS_DIR, filename)
        
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        
        # Usar gerador de relatórios
        periodo = f"{mes_inicio} a {mes_fim}" if mes_inicio and mes_fim else (mes or "Todos os períodos")
        success = report_gen.generate_excel_report(filepath, dados, metricas_gerais, dados_relatorio, periodo)
        
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

@app.get("/api/export/pdf")
async def export_pdf(
    client_id: int = 1,
    mes: Optional[str] = None,
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    upload_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Exporta relatório completo para PDF"""
    try:
        analytics = Analytics(db)
        report_gen = ReportGenerator()
        
        # Busca dados e métricas (igual à apresentação)
        insights_engine = InsightsEngine(db)
        
        # Busca todos os dados (igual à apresentação)
        metricas_gerais = analytics.metricas_gerais(client_id, mes_inicio, mes_fim, None, None)
        top_cids = analytics.top_cids(client_id, 10, mes_inicio, mes_fim, None, None)
        top_funcionarios = analytics.top_funcionarios(client_id, 10, mes_inicio, mes_fim, None, None)
        top_setores = analytics.top_setores(client_id, 10, mes_inicio, mes_fim, None, None)
        
        # Busca evolução mensal
        evolucao_mensal = []
        try:
            evolucao_mensal = analytics.evolucao_mensal(client_id, 12, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular evolução mensal: {e}")
        
        # Busca distribuição por gênero
        distribuicao_genero = []
        try:
            distribuicao_genero = analytics.distribuicao_genero(client_id, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular distribuição de gênero: {e}")
        
        # Busca top escalas
        top_escalas = []
        try:
            top_escalas = analytics.top_escalas(client_id, 10, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular top escalas: {e}")
        
        # Busca top motivos
        top_motivos = []
        try:
            top_motivos = analytics.top_motivos(client_id, 10, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular top motivos: {e}")
        
        # Busca dias por centro de custo
        dias_centro_custo = []
        try:
            dias_centro_custo = analytics.dias_perdidos_por_centro_custo(client_id, 10, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular dias por centro de custo: {e}")
        
        # Busca distribuição de dias
        distribuicao_dias = []
        try:
            distribuicao_dias = analytics.distribuicao_dias_por_atestado(client_id, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular distribuição de dias: {e}")
        
        # Busca média por CID
        media_cid = []
        try:
            media_cid = analytics.media_dias_por_cid(client_id, 10, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular média por CID: {e}")
        
        # Busca top CIDs para dias (dias por doença)
        top_cids_dias = []
        try:
            top_cids_dias = analytics.top_cids(client_id, 5, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular top CIDs para dias: {e}")
        
        # Busca dias por setor e gênero
        dias_setor_genero = []
        try:
            dias_setor_genero = analytics.dias_perdidos_setor_genero(client_id, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular dias por setor e gênero: {e}")
        
        # Busca insights gerais
        insights = []
        try:
            insights = insights_engine.gerar_insights(client_id)
        except Exception as e:
            print(f"Erro ao gerar insights gerais: {e}")
        
        # Adiciona análises de todos os gráficos
        tipos_graficos = [
            ('top_cids', top_cids, '📊', 'TOP 10 Doenças Mais Frequentes'),
            ('funcionarios_dias', top_funcionarios, '👤', 'Dias Perdidos por Funcionário'),
            ('evolucao_mensal', evolucao_mensal, '📈', 'Evolução Mensal'),
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
                    analise = insights_engine.gerar_analise_grafico(tipo_grafico, dados_grafico, metricas_gerais)
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
        
        # Preparar dados para relatório
        dados_relatorio = {
            'top_cids': top_cids,
            'top_funcionarios': top_funcionarios,
            'top_setores': top_setores,
            'evolucao_mensal': evolucao_mensal,
            'distribuicao_genero': distribuicao_genero,
            'top_escalas': top_escalas,
            'top_motivos': top_motivos,
            'dias_centro_custo': dias_centro_custo,
            'distribuicao_dias': distribuicao_dias,
            'media_cid': media_cid,
            'top_cids_dias': top_cids_dias,
            'dias_setor_genero': dias_setor_genero
        }
        
        # Gerar arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_absenteismo_{timestamp}.pdf"
        filepath = os.path.join(EXPORTS_DIR, filename)
        
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        
        # Gerar período
        periodo = f"{mes_inicio} a {mes_fim}" if mes_inicio and mes_fim else (mes or "Todos os períodos")
        
        # Gerar PDF com gráficos e insights
        success = report_gen.generate_pdf_report(filepath, dados_relatorio, metricas_gerais, insights, periodo, insights_engine)
        
        if not success:
            raise HTTPException(status_code=500, detail="Erro ao gerar relatório PDF")
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='application/pdf'
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao exportar PDF: {str(e)}")

@app.get("/api/export/pptx")
async def export_pptx(
    client_id: int = 1,
    mes: Optional[str] = None,
    mes_inicio: Optional[str] = None,
    mes_fim: Optional[str] = None,
    upload_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Exporta apresentação completa para PowerPoint"""
    try:
        analytics = Analytics(db)
        report_gen = ReportGenerator()
        
        # Busca dados e métricas (igual ao PDF)
        insights_engine = InsightsEngine(db)
        
        # Busca todos os dados (igual ao PDF)
        metricas_gerais = analytics.metricas_gerais(client_id, mes_inicio, mes_fim, None, None)
        top_cids = analytics.top_cids(client_id, 10, mes_inicio, mes_fim, None, None)
        top_funcionarios = analytics.top_funcionarios(client_id, 10, mes_inicio, mes_fim, None, None)
        top_setores = analytics.top_setores(client_id, 10, mes_inicio, mes_fim, None, None)
        
        # Busca evolução mensal
        evolucao_mensal = []
        try:
            evolucao_mensal = analytics.evolucao_mensal(client_id, 12, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular evolução mensal: {e}")
        
        # Busca distribuição por gênero
        distribuicao_genero = []
        try:
            distribuicao_genero = analytics.distribuicao_genero(client_id, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular distribuição de gênero: {e}")
        
        # Busca top escalas
        top_escalas = []
        try:
            top_escalas = analytics.top_escalas(client_id, 10, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular top escalas: {e}")
        
        # Busca top motivos
        top_motivos = []
        try:
            top_motivos = analytics.top_motivos(client_id, 10, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular top motivos: {e}")
        
        # Busca dias por centro de custo
        dias_centro_custo = []
        try:
            dias_centro_custo = analytics.dias_perdidos_por_centro_custo(client_id, 10, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular dias por centro de custo: {e}")
        
        # Busca distribuição de dias
        distribuicao_dias = []
        try:
            distribuicao_dias = analytics.distribuicao_dias_por_atestado(client_id, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular distribuição de dias: {e}")
        
        # Busca média por CID
        media_cid = []
        try:
            media_cid = analytics.media_dias_por_cid(client_id, 10, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular média por CID: {e}")
        
        # Busca top CIDs para dias (dias por doença)
        top_cids_dias = []
        try:
            top_cids_dias = analytics.top_cids(client_id, 5, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular top CIDs para dias: {e}")
        
        # Busca dias por setor e gênero
        dias_setor_genero = []
        try:
            dias_setor_genero = analytics.dias_perdidos_setor_genero(client_id, mes_inicio, mes_fim, None, None)
        except Exception as e:
            print(f"Erro ao calcular dias por setor e gênero: {e}")
        
        # Busca insights gerais
        insights = []
        try:
            insights = insights_engine.gerar_insights(client_id)
        except Exception as e:
            print(f"Erro ao gerar insights gerais: {e}")
        
        # Adiciona análises de todos os gráficos
        tipos_graficos = [
            ('top_cids', top_cids, '📊', 'TOP 10 Doenças Mais Frequentes'),
            ('funcionarios_dias', top_funcionarios, '👤', 'Dias Perdidos por Funcionário'),
            ('evolucao_mensal', evolucao_mensal, '📈', 'Evolução Mensal'),
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
                    analise = insights_engine.gerar_analise_grafico(tipo_grafico, dados_grafico, metricas_gerais)
                    if analise:
                        partes = analise.split('💡')
                        insights.append({
                            'tipo': 'analise',
                            'icone': icone,
                            'titulo': f'Análise: {titulo}',
                            'texto': partes[0].strip().replace('**', '') if len(partes) > 0 else analise.replace('**', ''),
                            'descricao': partes[0].strip().replace('**', '') if len(partes) > 0 else analise.replace('**', ''),
                            'recomendacao': partes[1].strip().replace('**', '').replace('💡', '').replace('Recomendação:', '').strip() if len(partes) > 1 else None
                        })
                except Exception as e:
                    print(f"Erro ao gerar análise para {tipo_grafico}: {e}")
        
        # Preparar dados para relatório
        dados_relatorio = {
            'top_cids': top_cids,
            'top_funcionarios': top_funcionarios,
            'top_setores': top_setores,
            'evolucao_mensal': evolucao_mensal,
            'distribuicao_genero': distribuicao_genero,
            'top_escalas': top_escalas,
            'top_motivos': top_motivos,
            'dias_centro_custo': dias_centro_custo,
            'distribuicao_dias': distribuicao_dias,
            'media_cid': media_cid,
            'top_cids_dias': top_cids_dias,
            'dias_setor_genero': dias_setor_genero
        }
        
        # Gerar arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"apresentacao_absenteismo_{timestamp}.pptx"
        filepath = os.path.join(EXPORTS_DIR, filename)
        
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        
        # Gerar período
        periodo = f"{mes_inicio} a {mes_fim}" if mes_inicio and mes_fim else (mes or "Todos os períodos")
        
        # Gerar PowerPoint com gráficos e insights
        success = report_gen.generate_powerpoint_report(filepath, dados_relatorio, metricas_gerais, insights, periodo, insights_engine)
        
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
    client_id: int = 1,
    periodo1_inicio: str = Query(...),
    periodo1_fim: str = Query(...),
    periodo2_inicio: str = Query(...),
    periodo2_fim: str = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Compara dois períodos e retorna métricas e variações"""
    try:
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
async def perfil_funcionario_page(current_user: User = Depends(get_current_active_user)):
    """Página de perfil de funcionário"""
    file_path = os.path.join(FRONTEND_DIR, "perfil_funcionario.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/funcionario/perfil")
async def perfil_funcionario(
    nome: str = Query(...),
    client_id: int = 1,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retorna perfil completo de um funcionário"""
    try:
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
    client_id: int = 1,
    upload_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Lista todos os dados com filtros"""
    try:
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
                
                # Cria registro com os novos campos da planilha padronizada
                registro = {
                    'id': a.id,
                    'upload_id': a.upload_id,
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
    db: Session = Depends(get_db)
):
    """Obtém um registro específico"""
    atestado = db.query(Atestado).filter(Atestado.id == atestado_id).first()
    
    if not atestado:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    """Atualiza um registro"""
    atestado = db.query(Atestado).filter(Atestado.id == atestado_id).first()
    
    if not atestado:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    
    try:
        for key, value in dados.items():
            if hasattr(atestado, key):
                setattr(atestado, key, value)
        
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/dados/{atestado_id}")
async def excluir_dado(
    atestado_id: int,
    db: Session = Depends(get_db)
):
    """Exclui um registro"""
    atestado = db.query(Atestado).filter(Atestado.id == atestado_id).first()
    
    if not atestado:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    
    try:
        db.delete(atestado)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

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
    client_id: int = Form(1),
    db: Session = Depends(get_db)
):
    """Processa arquivo com configurações das colunas"""
    try:
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
