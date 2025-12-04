@echo off
chcp 65001 > nul
cls

echo ========================================
echo  DEPLOY - Servidor de Producao
echo ========================================
echo.

set SERVIDOR_IP=72.60.166.55
set PORTA_SSH=65002

echo Servidor: %SERVIDOR_IP%:%PORTA_SSH%
echo.

set /p USUARIO_SSH="Digite o usuario SSH: "

if "%USUARIO_SSH%"=="" (
    echo [ERRO] Usuario SSH e obrigatorio!
    pause
    exit /b 1
)

echo.
echo Escolha o caminho do sistema no servidor:
echo 1. ~/domains/absenteismocontroller.com.br/public_html/absenteismo
echo 2. ~/public_html/absenteismo
echo.
set /p OPCAO="Opcao [1]: "

if "%OPCAO%"=="" set OPCAO=1

if "%OPCAO%"=="1" (
    set CAMINHO=~/domains/absenteismocontroller.com.br/public_html/absenteismo
) else if "%OPCAO%"=="2" (
    set CAMINHO=~/public_html/absenteismo
) else (
    set CAMINHO=~/domains/absenteismocontroller.com.br/public_html/absenteismo
)

echo.
echo ========================================
echo  Conectando ao servidor...
echo ========================================
echo.
echo Caminho: %CAMINHO%
echo.
echo ATENCAO: Voce sera solicitado a inserir a senha SSH
echo.

ssh -p %PORTA_SSH% %USUARIO_SSH%@%SERVIDOR_IP% "cd %CAMINHO% && git pull origin main && echo '=== DEPLOY CONCLUIDO ==='"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  DEPLOY CONCLUIDO COM SUCESSO!
    echo ========================================
    echo.
    echo O servidor foi atualizado!
    echo Verifique o site: https://www.absenteismocontroller.com.br
    echo.
) else (
    echo.
    echo ========================================
    echo  FALHA NO DEPLOY
    echo ========================================
    echo.
    echo Tente manualmente:
    echo   ssh -p %PORTA_SSH% %USUARIO_SSH%@%SERVIDOR_IP%
    echo   cd %CAMINHO%
    echo   git pull origin main
    echo.
)

pause



