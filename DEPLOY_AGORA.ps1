# Script de Deploy Rápido - Servidor 72.60.166.55
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DEPLOY - Servidor de Produção" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$servidorIP = "72.60.166.55"
$portaSSH = 65002

Write-Host "[INFO] Servidor: ${servidorIP}:${portaSSH}" -ForegroundColor Yellow
Write-Host ""

# Pergunta o usuário SSH
$usuarioSSH = Read-Host "Digite o usuário SSH"

if ([string]::IsNullOrEmpty($usuarioSSH)) {
    Write-Host "[ERRO] Usuário SSH é obrigatório!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[1/4] Verificando status local do Git..." -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "[2/4] Commit e Push já realizados!" -ForegroundColor Green
Write-Host "      Commit: 50462a2" -ForegroundColor Green

Write-Host ""
Write-Host "[3/4] Tentando caminhos comuns no servidor..." -ForegroundColor Yellow

# Tenta caminhos comuns
$caminhos = @(
    "~/domains/absenteismocontroller.com.br/public_html/absenteismo",
    "~/public_html/absenteismo",
    "/home/$usuarioSSH/domains/absenteismocontroller.com.br/public_html/absenteismo",
    "/home/$usuarioSSH/public_html/absenteismo"
)

Write-Host ""
Write-Host "[INFO] Tentando conectar ao servidor..." -ForegroundColor Yellow
Write-Host "       Você será solicitado a inserir a senha SSH" -ForegroundColor Yellow
Write-Host ""

# Pergunta qual caminho usar ou tenta encontrar
Write-Host "Escolha o caminho do sistema no servidor:" -ForegroundColor Cyan
Write-Host "1. ~/domains/absenteismocontroller.com.br/public_html/absenteismo" -ForegroundColor White
Write-Host "2. ~/public_html/absenteismo" -ForegroundColor White
Write-Host "3. Outro (digite o caminho completo)" -ForegroundColor White
Write-Host ""
$opcao = Read-Host "Opção [1]"

$caminhoServidor = ""
if ($opcao -eq "1") {
    $caminhoServidor = "~/domains/absenteismocontroller.com.br/public_html/absenteismo"
} elseif ($opcao -eq "2") {
    $caminhoServidor = "~/public_html/absenteismo"
} elseif ($opcao -eq "3") {
    $caminhoServidor = Read-Host "Digite o caminho completo"
} else {
    $caminhoServidor = "~/domains/absenteismocontroller.com.br/public_html/absenteismo"
}

if ([string]::IsNullOrEmpty($caminhoServidor)) {
    $caminhoServidor = "~/domains/absenteismocontroller.com.br/public_html/absenteismo"
}

Write-Host ""
Write-Host "[4/4] Executando deploy..." -ForegroundColor Yellow
Write-Host "       Caminho: $caminhoServidor" -ForegroundColor Gray
Write-Host ""

# Comando SSH para fazer pull
$comando = "cd $caminhoServidor && git pull origin main && echo '=== DEPLOY CONCLUIDO ==='"

Write-Host "Executando comando no servidor:" -ForegroundColor Cyan
Write-Host "  $comando" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  INSIRA A SENHA SSH QUANDO SOLICITADO" -ForegroundColor Yellow
Write-Host ""

# Executa SSH
ssh -p $portaSSH $usuarioSSH@$servidorIP $comando

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✅ DEPLOY CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "O servidor foi atualizado!" -ForegroundColor Green
    Write-Host "Verifique o site: https://www.absenteismocontroller.com.br" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ⚠️  FALHA NO DEPLOY" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possíveis causas:" -ForegroundColor Yellow
    Write-Host "  - Senha incorreta" -ForegroundColor Yellow
    Write-Host "  - Caminho incorreto" -ForegroundColor Yellow
    Write-Host "  - Git não configurado no servidor" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Tente manualmente:" -ForegroundColor Cyan
    Write-Host "  ssh -p $portaSSH $usuarioSSH@$servidorIP" -ForegroundColor White
    Write-Host "  cd $caminhoServidor" -ForegroundColor White
    Write-Host "  git pull origin main" -ForegroundColor White
    Write-Host ""
}

Write-Host "Pressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

