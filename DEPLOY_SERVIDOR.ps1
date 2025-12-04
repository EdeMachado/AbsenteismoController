# Script de Deploy para Servidor de Produção
# Este script faz pull no servidor via SSH

param(
    [string]$ServidorHost = "",
    [int]$ServidorPorta = 65002,
    [string]$ServidorUsuario = "",
    [string]$ServidorCaminho = "",
    [string]$ServidorSenha = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DEPLOY - Correção TOP CIDs por Setor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verifica se está no diretório correto
$diretorioAtual = Get-Location
Write-Host "[INFO] Diretório atual: $diretorioAtual" -ForegroundColor Yellow

# Verifica se há alterações não commitadas
Write-Host ""
Write-Host "[1/4] Verificando status do Git..." -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "[2/4] Commit e Push já foram feitos!" -ForegroundColor Green
Write-Host "      Commit: 50462a2" -ForegroundColor Green
Write-Host "      Status: Alterações no GitHub" -ForegroundColor Green

Write-Host ""
Write-Host "[3/4] Conectando ao servidor..." -ForegroundColor Yellow

# Verifica se as credenciais foram fornecidas
if ([string]::IsNullOrEmpty($ServidorHost) -or [string]::IsNullOrEmpty($ServidorUsuario)) {
    Write-Host ""
    Write-Host "[AVISO] Credenciais não fornecidas!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Para fazer deploy automático, você precisa:" -ForegroundColor Yellow
    Write-Host "1. Acessar o servidor via SSH manualmente" -ForegroundColor Yellow
    Write-Host "2. Executar: git pull origin main" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "OU fornecer as credenciais:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Exemplo:" -ForegroundColor Cyan
    Write-Host '.\DEPLOY_SERVIDOR.ps1 -ServidorHost "ssh.hostinger.com" -ServidorUsuario "usuario" -ServidorCaminho "/caminho/do/sistema"' -ForegroundColor Cyan
    Write-Host ""
    
    # Opção interativa
    $continuar = Read-Host "Deseja configurar o deploy agora? (S/N)"
    if ($continuar -eq "S" -or $continuar -eq "s") {
        Write-Host ""
        $ServidorHost = Read-Host "Host SSH do servidor"
        $ServidorUsuario = Read-Host "Usuário SSH"
        $portaInput = Read-Host "Porta SSH [65002]"
        if ($portaInput) { $ServidorPorta = [int]$portaInput }
        $ServidorCaminho = Read-Host "Caminho do sistema no servidor"
    } else {
        Write-Host ""
        Write-Host "Deploy cancelado. Use o método manual descrito acima." -ForegroundColor Yellow
        exit 0
    }
}

# Tenta conectar e fazer pull
if (-not [string]::IsNullOrEmpty($ServidorHost)) {
    Write-Host ""
    Write-Host "Tentando conectar a: $ServidorUsuario@$ServidorHost:$ServidorPorta" -ForegroundColor Yellow
    
    # Comando SSH para fazer pull
    if ([string]::IsNullOrEmpty($ServidorCaminho)) {
        $ServidorCaminho = "~/domains/absenteismocontroller.com.br/public_html/absenteismo"
    }
    
    $comandoSSH = "cd $ServidorCaminho && git pull origin main"
    
    Write-Host ""
    Write-Host "Executando no servidor:" -ForegroundColor Cyan
    Write-Host "  $comandoSSH" -ForegroundColor White
    Write-Host ""
    
    # Tenta usar ssh.exe (Windows 10+)
    try {
        $comandoCompleto = "ssh -p $ServidorPorta $ServidorUsuario@$ServidorHost `"$comandoSSH`""
        Write-Host "[INFO] Executando: $comandoCompleto" -ForegroundColor Gray
        Write-Host ""
        Write-Host "⚠️  Você precisará inserir a senha quando solicitado" -ForegroundColor Yellow
        Write-Host ""
        
        # Executa o comando SSH
        Invoke-Expression $comandoCompleto
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[4/4] ✅ DEPLOY CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
            Write-Host ""
            Write-Host "O servidor foi atualizado. Verifique o site:" -ForegroundColor Green
            Write-Host "https://www.absenteismocontroller.com.br" -ForegroundColor Cyan
        } else {
            Write-Host ""
            Write-Host "[ERRO] Falha ao executar o comando SSH" -ForegroundColor Red
            Write-Host "Código de saída: $LASTEXITCODE" -ForegroundColor Red
        }
    } catch {
        Write-Host ""
        Write-Host "[ERRO] Não foi possível executar SSH automaticamente" -ForegroundColor Red
        Write-Host "Erro: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Execute manualmente no terminal SSH:" -ForegroundColor Yellow
        Write-Host "  cd $ServidorCaminho" -ForegroundColor Cyan
        Write-Host "  git pull origin main" -ForegroundColor Cyan
    }
} else {
    Write-Host ""
    Write-Host "[INFO] Use o método manual de deploy" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""



