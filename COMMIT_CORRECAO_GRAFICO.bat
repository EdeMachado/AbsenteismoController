@echo off
echo ========================================
echo COMMIT CORRECAO TOP CIDs POR SETOR
echo ========================================
echo.

cd "C:\Users\Ede Machado\AbsenteismoConverplast"

echo Adicionando arquivos corrigidos...
git add frontend/index.html
git add frontend/static/js/dashboard.js

echo.
echo Fazendo commit...
git commit -m "Correção: TOP CIDs por Setor - Transformado cards em gráfico de barras"

echo.
echo Fazendo push...
git push origin main

echo.
echo ========================================
echo CONCLUIDO!
echo ========================================
echo.
echo Agora você precisa atualizar no servidor.
echo Se o servidor faz pull automático, aguarde alguns segundos.
echo Se nao, acesse o servidor e execute: git pull
echo.
pause



