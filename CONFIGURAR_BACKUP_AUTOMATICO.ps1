# Script PowerShell para configurar backup automatico no Task Scheduler
# Execute como Administrador: PowerShell -ExecutionPolicy Bypass -File CONFIGURAR_BACKUP_AUTOMATICO.ps1

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURAR BACKUP AUTOMATICO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verifica se esta executando como administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ATENCAO: Este script precisa ser executado como Administrador!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Clique com botao direito no PowerShell e escolha 'Executar como Administrador'" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

# Obtem o diretorio atual (onde esta o script)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backupScript = Join-Path $scriptDir "BACKUP_AUTOMATICO.bat"
$pythonScript = Join-Path $scriptDir "backup_automatico.py"

# Verifica se os arquivos existem
if (-not (Test-Path $backupScript)) {
    Write-Host "ERRO: Arquivo nao encontrado: $backupScript" -ForegroundColor Red
    pause
    exit 1
}

if (-not (Test-Path $pythonScript)) {
    Write-Host "ERRO: Arquivo nao encontrado: $pythonScript" -ForegroundColor Red
    pause
    exit 1
}

# Encontra Python
$pythonPath = $null
$pythonCommands = @("python", "python3", "py")

foreach ($cmd in $pythonCommands) {
    try {
        $result = Get-Command $cmd -ErrorAction Stop
        $pythonPath = $result.Source
        break
    } catch {
        continue
    }
}

if (-not $pythonPath) {
    Write-Host "ERRO: Python nao encontrado no PATH!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor, instale Python ou adicione ao PATH do sistema." -ForegroundColor Yellow
    Write-Host "Ou configure manualmente o caminho do Python no Task Scheduler." -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host "OK: Python encontrado: $pythonPath" -ForegroundColor Green
Write-Host ""

# Nome da tarefa
$taskName = "AbsenteismoController_BackupAutomatico"

# Verifica se a tarefa ja existe
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "ATENCAO: Tarefa ja existe: $taskName" -ForegroundColor Yellow
    Write-Host ""
    $resposta = Read-Host "Deseja substituir a tarefa existente? (S/N)"
    if ($resposta -ne "S" -and $resposta -ne "s") {
        Write-Host "Operacao cancelada." -ForegroundColor Yellow
        pause
        exit 0
    }
    
    # Remove tarefa existente
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "OK: Tarefa antiga removida" -ForegroundColor Green
    Write-Host ""
}

# Cria a acao (executar o script .bat)
$action = New-ScheduledTaskAction -Execute $backupScript -WorkingDirectory $scriptDir

# Cria o trigger (diario as 02:00)
$trigger = New-ScheduledTaskTrigger -Daily -At 2am

# Configuracoes da tarefa
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -MultipleInstances IgnoreNew

# Cria o principal (executar mesmo quando usuario nao estiver logado)
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

# Registra a tarefa
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Backup automatico diario do banco de dados AbsenteismoController" | Out-Null
    
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  BACKUP AUTOMATICO CONFIGURADO!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Detalhes da tarefa:" -ForegroundColor Cyan
    Write-Host "   Nome: $taskName" -ForegroundColor White
    Write-Host "   Frequencia: Diario as 02:00" -ForegroundColor White
    Write-Host "   Script: $backupScript" -ForegroundColor White
    Write-Host "   Retencao: 7 dias (limpeza automatica)" -ForegroundColor White
    Write-Host ""
    Write-Host "Para modificar a tarefa:" -ForegroundColor Yellow
    Write-Host "   1. Abra o Agendador de Tarefas (Task Scheduler)" -ForegroundColor White
    Write-Host "   2. Procure por: $taskName" -ForegroundColor White
    Write-Host "   3. Clique com botao direito e escolha Propriedades" -ForegroundColor White
    Write-Host ""
    Write-Host "Logs serao salvos em: logs\backup.log" -ForegroundColor Cyan
    Write-Host ""
    
} catch {
    Write-Host "ERRO ao criar tarefa: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Tente executar manualmente:" -ForegroundColor Yellow
    Write-Host "   1. Abra o Agendador de Tarefas" -ForegroundColor White
    Write-Host "   2. Crie uma tarefa basica" -ForegroundColor White
    Write-Host "   3. Configure para executar: $backupScript" -ForegroundColor White
    Write-Host "   4. Configure para executar diariamente as 02:00" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Write-Host "Pressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
