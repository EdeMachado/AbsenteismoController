@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    🎨 GERANDO ÍCONE .ICO
echo ========================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo Por favor, instale Python primeiro:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo 📦 Instalando dependências (se necessário)...
python -m pip install Pillow --quiet --disable-pip-version-check

echo.
echo 🔄 Gerando ícone...
echo.

python gerar_ico_simples.py

if errorlevel 1 (
    echo.
    echo ❌ Erro ao gerar ícone!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    ✅ CONCLUÍDO COM SUCESSO!
echo ========================================
echo.
echo 📁 Arquivo criado:
echo    frontend\static\favicon.ico
echo.
echo 💡 Para usar no atalho do desktop:
echo    1. Clique direito no atalho
echo    2. Propriedades ^> Alterar Ícone...
echo    3. Navegue até: frontend\static\favicon.ico
echo.
pause



