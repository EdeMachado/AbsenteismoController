@echo off
chcp 65001 > nul
cls

echo.
echo ========================================
echo  ABSENTEÍSMO CONTROLLER - INSTALADOR
echo  GrupoBiomed
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
    echo Após instalar, execute este arquivo novamente.
    echo.
    pause
    exit /b 1
)

echo [1/4] Instalando dependências do Electron...
call npm install
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependências!
    pause
    exit /b 1
)

echo.
echo [2/4] Compilando aplicativo...
call npm run build-win
if errorlevel 1 (
    echo [ERRO] Falha ao compilar!
    pause
    exit /b 1
)

echo.
echo [3/4] Verificando arquivos compilados...
if not exist "dist\AbsenteismoController Setup *.exe" (
    echo [AVISO] Instalador não encontrado. Verificando versão portátil...
    if not exist "dist\AbsenteismoController-Portable.exe" (
        echo [ERRO] Nenhum executável encontrado!
        pause
        exit /b 1
    ) else (
        echo [OK] Versão portátil encontrada!
        echo.
        echo O arquivo está em: dist\AbsenteismoController-Portable.exe
        echo Você pode copiar este arquivo para qualquer lugar e executar.
    )
) else (
    echo [OK] Instalador encontrado!
    echo.
    echo O instalador está em: dist\
    echo Execute o arquivo .exe para instalar o app.
)

echo.
echo [4/4] Concluído!
echo.
echo ========================================
echo  PRÓXIMOS PASSOS:
echo ========================================
echo.
echo 1. Vá até a pasta: dist\
echo 2. Execute o instalador .exe
echo 3. Siga o assistente de instalação
echo 4. O app aparecerá no menu Iniciar
echo.
pause



