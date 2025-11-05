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
from collections import OrderedDict
import pandas as pd

from .database import get_db, init_db
from .models import Client, Upload, Atestado
from .excel_processor import ExcelProcessor
from .analytics import Analytics
from .insights import InsightsEngine
import requests
import re
from pydantic import BaseModel

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

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

# Initialize database
@app.on_event("startup")
async def startup_event():
    init_db()
    # Cria cliente padrão se não existir
    db = next(get_db())
    client = db.query(Client).filter(Client.id == 1).first()
    if not client:
        client = Client(id=1, nome="GrupoBiomed", cnpj="00.000.000/0001-00")
        db.add(client)
        db.commit()
    db.close()

# ==================== ROUTES - FRONTEND ====================

@app.get("/", response_class=HTMLResponse)
async def index():
    """Página principal"""
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

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    client_id: int = 1,
    db: Session = Depends(get_db)
):
    """Upload de planilha"""
    try:
        # Salva arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOADS_DIR, filename)
        
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
            filename=file.filename,
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
            "insights": insights
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

# ==================== MÓDULO CLIENTES ====================

class ClienteCreate(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    nome_fantasia: Optional[str] = None
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
                "created_at": c.created_at.isoformat() if c.created_at else None,
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
        
        novo_cliente = Client(
            nome=cliente.nome,
            cnpj=re.sub(r'\D', '', cliente.cnpj) if cliente.cnpj else None,
            nome_fantasia=cliente.nome_fantasia,
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

@app.delete("/api/clientes/{cliente_id}")
async def deletar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Deleta um cliente"""
    try:
        cliente = db.query(Client).filter(Client.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Verifica se tem uploads
        if len(cliente.uploads) > 0:
            raise HTTPException(status_code=400, detail="Não é possível deletar cliente com uploads cadastrados")
        
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
    upload_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Exporta dados tratados para Excel"""
    import pandas as pd
    from datetime import datetime
    
    query = db.query(Atestado).join(Upload).filter(Upload.client_id == client_id)
    
    if upload_id:
        query = query.filter(Upload.id == upload_id)
    elif mes:
        query = query.filter(Upload.mes_referencia == mes)
    
    atestados = query.all()
    
    if not atestados:
        raise HTTPException(status_code=404, detail="Nenhum dado encontrado")
    
    # Converter para DataFrame
    dados = []
    for a in atestados:
        dados.append({
            'Nome': a.nome_funcionario,
            'CPF': a.cpf,
            'Setor': a.setor,
            'Cargo': a.cargo,
            'Gênero': a.genero,
            'Data Afastamento': a.data_afastamento,
            'Data Retorno': a.data_retorno,
            'Tipo': a.tipo_atestado,
            'CID': a.cid,
            'Descrição CID': a.descricao_cid,
            'Dias Atestado': a.numero_dias_atestado,
            'Horas Atestado': a.numero_horas_atestado,
            'Dias Perdidos': a.dias_perdidos,
            'Horas Perdidas': a.horas_perdidas
        })
    
    df = pd.DataFrame(dados)
    
    # Salvar arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"absenteismo_tratado_{timestamp}.xlsx"
    filepath = os.path.join(EXPORTS_DIR, filename)
    
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    df.to_excel(filepath, index=False)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

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
    client_id: int = 1,
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
