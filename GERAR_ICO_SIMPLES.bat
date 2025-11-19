@echo off
chcp 65001 >nul
echo ========================================
echo 🎨 GERANDO ÍCONE .ICO
echo ========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo Por favor, instale Python primeiro.
    pause
    exit /b 1
)

REM Instala dependências se necessário
echo 📦 Verificando dependências...
python -m pip install Pillow cairosvg --quiet

REM Executa o script
python gerar_ico.py

echo.
echo ========================================
echo ✅ CONCLUÍDO!
echo ========================================
echo.
echo 📁 O arquivo favicon.ico está em:
echo    frontend\static\favicon.ico
echo.
pause



