# Deploy via PowerShell - Execute este arquivo

$servidor = "72.60.166.55"
$porta = "65002"
$caminho = "~/domains/absenteismocontroller.com.br/public_html/absenteismo"

Write-Host "Digite seu usuario SSH:" -ForegroundColor Yellow
$usuario = Read-Host

Write-Host "`nConectando ao servidor..." -ForegroundColor Cyan
ssh -p $porta "$usuario@$servidor" "cd $caminho && git pull origin main"

Write-Host "`nDeploy concluido!" -ForegroundColor Green

