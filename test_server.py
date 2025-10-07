#!/usr/bin/env python3
"""
Script simples para testar o servidor
"""
import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from backend.main import app
    import uvicorn
    
    print("✅ Módulos importados com sucesso!")
    print("🚀 Iniciando servidor...")
    print("📱 Acesse: http://localhost:8000")
    print("⏹️  Pressione Ctrl+C para parar")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
