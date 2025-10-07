"""
FastAPI Main Application - AbsenteismoController v2.0
"""
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import shutil
import json
from datetime import datetime

from .database import get_db, init_db
from .models import Client, Upload, Atestado
from .excel_processor import ExcelProcessor
from .analytics import Analytics
from .insights import InsightsEngine

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
    db: Session = Depends(get_db)
):
    """Dashboard principal"""
    analytics = Analytics(db)
    insights_engine = InsightsEngine(db)
    
    metricas = analytics.metricas_gerais(client_id, mes_inicio, mes_fim)
    top_cids = analytics.top_cids(client_id, 10, mes_inicio, mes_fim)
    top_setores = analytics.top_setores(client_id, 5, mes_inicio, mes_fim)
    evolucao = analytics.evolucao_mensal(client_id, 12)
    distribuicao_genero = analytics.distribuicao_genero(client_id, mes_inicio, mes_fim)
    insights = insights_engine.gerar_insights(client_id)
    
    resultado = {
        "metricas": metricas,
        "top_cids": top_cids,
        "top_setores": top_setores,
        "evolucao_mensal": evolucao,
        "distribuicao_genero": distribuicao_genero,
        "insights": insights
    }
    
    # Corrige encoding antes de retornar
    return corrigir_encoding_json(resultado)

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
    return analytics.top_funcionarios(client_id, 50, mes_inicio, mes_fim)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
