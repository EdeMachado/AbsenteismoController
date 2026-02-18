@echo off
chcp 65001 > nul
REM Script para executar backup automático
REM Este script será chamado pelo Task Scheduler do Windows

cd /d "%~dp0"
python backup_automatico.py

REM Se Python não estiver no PATH, tente com caminho completo
if errorlevel 1 (
    echo Tentando com python3...
    python3 backup_automatico.py
)

if errorlevel 1 (
    echo.
    echo ========================================
    echo ERRO: Python nao encontrado!
    echo ========================================
    echo.
    echo Configure o caminho completo do Python no Task Scheduler
    echo ou adicione Python ao PATH do sistema.
    echo.
    pause
    exit /b 1
)

exit /b 0

