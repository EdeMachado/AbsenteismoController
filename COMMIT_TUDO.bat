@echo off
echo ========================================
echo COMMIT DE TODAS AS ALTERACOES
echo ========================================
echo.

cd "C:\Users\Ede Machado\AbsenteismoConverplast"

echo Adicionando TODOS os arquivos...
git add -A

echo.
echo Fazendo commit...
git commit -m "Correções completas: upload, apresentação, botões, gráficos, barra rolagem, segurança"

echo.
echo Fazendo push...
git push origin main

echo.
echo ========================================
echo CONCLUIDO!
echo ========================================
pause


