@echo off
chcp 65001 > nul
cls

echo.
echo ========================================
echo  ABSENTEÍSMO CONTROLLER v2.0
echo  GrupoBiomed
echo ========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python não encontrado!
    echo Por favor, instale o Python 3.10 ou superior.
    echo.
    pause
    exit /b 1
)

echo Verificando dependências...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Dependências não encontradas!
    echo Instalando dependências...
    pip install -r requirements.txt
    echo.
)

echo.
echo ========================================
echo Iniciando servidor...
echo ========================================
echo.
echo ✓ Servidor iniciando na porta 8000
echo ✓ Abrindo navegador automaticamente...
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

cd /d "%~dp0"

REM Aguarda 3 segundos e abre o navegador
start "" "http://localhost:8000"

REM Inicia o servidor
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

echo.
echo Servidor encerrado.
pause

