@echo off
chcp 65001 > nul
cls

echo.
echo ========================================
echo  INSTALAR APP DESKTOP
echo  AbsenteismoController v2.0
echo ========================================
echo.

REM Verifica se Node.js está instalado
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Node.js não encontrado!
    echo.
    echo Por favor, instale o Node.js 18 ou superior:
    echo https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo [1/3] Instalando dependências...
call npm install
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependências!
    pause
    exit /b 1
)

echo.
echo [2/3] Compilando aplicativo...
call npm run build-win
if errorlevel 1 (
    echo [ERRO] Falha ao compilar!
    pause
    exit /b 1
)

echo.
echo [3/3] Concluído!
echo.
echo O executável está em: app-desktop\dist\
echo.
echo Você pode:
echo - Executar o instalador .exe
echo - Ou usar a versão portátil
echo.
pause



