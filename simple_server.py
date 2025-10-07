#!/usr/bin/env python3
"""
Servidor simples sem emojis
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="AbsenteismoController", version="2.0.0")

@app.get("/")
async def root():
    return {"message": "AbsenteismoController v2.0"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

if __name__ == "__main__":
    print("Iniciando servidor...")
    print("Acesse: http://localhost:8000")
    print("Pressione Ctrl+C para parar")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
