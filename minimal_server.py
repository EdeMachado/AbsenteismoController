#!/usr/bin/env python3
"""
Servidor mínimo para testar
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    print("🚀 Iniciando servidor mínimo...")
    print("📱 Acesse: http://localhost:8000")
    print("⏹️  Pressione Ctrl+C para parar")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
