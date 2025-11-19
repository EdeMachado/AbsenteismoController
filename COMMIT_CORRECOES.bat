@echo off
echo ========================================
echo COMMIT DAS CORRECOES DE HOJE
echo ========================================
echo.

cd "C:\Users\Ede Machado\AbsenteismoConverplast"

echo Adicionando arquivos principais...
git add backend/main.py
git add backend/logger.py
git add backend/auth.py
git add backend/database.py
git add frontend/apresentacao.html
git add frontend/static/js/apresentacao.js
git add frontend/static/js/upload.js
git add frontend/index.html
git add frontend/clientes.html
git add frontend/configuracoes.html
git add frontend/static/css/main.css
git add frontend/static/js/auth.js
git add frontend/static/js/configuracoes.js
git add requirements.txt

echo.
echo Fazendo commit...
git commit -m "Correções: upload, apresentação, botões navegação, gráfico evolução mensal, barra rolagem intervenção"

echo.
echo Fazendo push...
git push origin main

echo.
echo ========================================
echo CONCLUIDO!
echo ========================================
pause


