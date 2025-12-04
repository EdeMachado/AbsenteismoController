# Deploy da Correção - TOP CIDs por Setor
# Caminho do servidor: /var/www/absenteismo

cd "C:\Users\Ede Machado\AbsenteismoConverplast"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DEPLOY - Correção Gráfico TOP CIDs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[INFO] Enviando arquivos corrigidos..." -ForegroundColor Yellow
Write-Host ""

# Deploy FRONTEND - Arquivos corrigidos
Write-Host "Enviando frontend/index.html..." -ForegroundColor Green
scp frontend/index.html root@72.60.166.55:/var/www/absenteismo/frontend/index.html

Write-Host "Enviando frontend/static/js/dashboard.js..." -ForegroundColor Green
scp frontend/static/js/dashboard.js root@72.60.166.55:/var/www/absenteismo/frontend/static/js/dashboard.js

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  DEPLOY CONCLUIDO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Verifique o site: https://www.absenteismocontroller.com.br" -ForegroundColor Cyan
Write-Host ""



