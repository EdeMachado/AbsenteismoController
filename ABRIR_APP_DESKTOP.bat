@echo off
chcp 65001 > nul
cls

echo.
echo ========================================
echo  ABSENTEÍSMO CONTROLLER - APP DESKTOP
echo  GrupoBiomed
echo ========================================
echo.

REM Abre o Chrome em modo app (se instalado)
set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
set CHROME_PATH_X86="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

if exist %CHROME_PATH% (
    echo Abrindo no Chrome em modo app...
    start "" %CHROME_PATH% --app=https://www.absenteismocontroller.com.br/landing --new-window
    goto :end
)

if exist %CHROME_PATH_X86% (
    echo Abrindo no Chrome em modo app...
    start "" %CHROME_PATH_X86% --app=https://www.absenteismocontroller.com.br/landing --new-window
    goto :end
)

REM Se Chrome não encontrado, abre no navegador padrão
echo Chrome não encontrado. Abrindo no navegador padrão...
start https://www.absenteismocontroller.com.br/landing

:end
echo.
echo App aberto!
echo Feche esta janela.
timeout /t 3 >nul

