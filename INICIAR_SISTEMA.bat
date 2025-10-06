@echo off
chcp 65001 > nul
cls

echo.
echo ========================================
echo  ABSENTEÍSMO CONTROLLER v2.0
echo  GrupoBiomed
echo ========================================
echo.
echo Iniciando servidor...
echo.
echo Acesse: http://localhost:8000
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

cd /d "%~dp0"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

pause
