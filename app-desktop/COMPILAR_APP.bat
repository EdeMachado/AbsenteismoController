@echo off
chcp 65001 > nul
cls

echo.
echo ========================================
echo  COMPILAR APP DESKTOP
echo  AbsenteismoController
echo ========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python não encontrado!
    echo Por favor, instale o Python 3.10 ou superior.
    pause
    exit /b 1
)

echo [1/3] Instalando PyInstaller...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar PyInstaller!
    pause
    exit /b 1
)

echo.
echo [2/3] Compilando executável...
cd /d "%~dp0"

REM Compila o executável
pyinstaller --onefile --windowed --name="AbsenteismoController" --clean app.py

if errorlevel 1 (
    echo [ERRO] Falha ao compilar!
    pause
    exit /b 1
)

echo.
echo [3/3] Concluído!
echo.
echo ========================================
echo  EXECUTÁVEL CRIADO!
echo ========================================
echo.
echo O arquivo está em: dist\AbsenteismoController.exe
echo.
echo Você pode:
echo - Copiar para qualquer lugar
echo - Criar atalho na área de trabalho
echo - Renomear se quiser
echo.
pause



