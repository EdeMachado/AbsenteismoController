# Script de Deploy Manual - PowerShell
# Execute este script no PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DEPLOY MANUAL - Correções" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navega para o diretório do projeto
Set-Location "C:\Users\Ede Machado\AbsenteismoConverplast"

Write-Host "[1/4] Verificando status..." -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "[2/4] Adicionando arquivos..." -ForegroundColor Yellow
git add frontend/static/js/produtividade.js
git add frontend/dados_powerbi.html
git add frontend/static/js/dados_powerbi.js

Write-Host ""
Write-Host "[3/4] Fazendo commit..." -ForegroundColor Yellow
$commitMsg = @"
Correção: Edição produtividade + Filtro ordenação em Meus Dados

- Corrigido problema de edição no módulo produtividade (client_id faltando)
- Adicionado filtro de ordenação crescente/decrescente no módulo Meus Dados
- Melhorias na interface de ordenação
"@

git commit -m $commitMsg

if ($LASTEXITCODE -ne 0) {
    Write-Host "[AVISO] Nenhuma alteração para commitar ou commit já existe" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[4/4] Fazendo push para GitHub..." -ForegroundColor Yellow
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✅ PUSH CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Agora faça o deploy no servidor:" -ForegroundColor Cyan
    Write-Host "  ssh -p 65002 SEU_USUARIO@72.60.166.55" -ForegroundColor White
    Write-Host "  cd ~/domains/absenteismocontroller.com.br/public_html/absenteismo" -ForegroundColor White
    Write-Host "  git pull origin main" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[ERRO] Falha ao fazer push!" -ForegroundColor Red
}

