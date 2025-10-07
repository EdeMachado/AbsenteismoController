#!/usr/bin/env python3
"""
Script de teste para verificar se há erros
"""
import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("🔍 Testando importações...")
    
    print("✅ Importando FastAPI...")
    from fastapi import FastAPI
    
    print("✅ Importando SQLAlchemy...")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    print("✅ Importando módulos do backend...")
    from backend.database import init_db, get_db
    from backend.models import Client, Upload, Atestado
    from backend.excel_processor import ExcelProcessor
    from backend.analytics import Analytics
    from backend.insights import InsightsEngine
    
    print("✅ Importando uvicorn...")
    import uvicorn
    
    print("🎉 Todas as importações funcionaram!")
    print("🚀 Iniciando servidor...")
    
    # Cria app
    app = FastAPI(title="AbsenteismoController", version="2.0.0")
    
    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "2.0.0"}
    
    # Inicia servidor
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
