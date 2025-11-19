# Script para criar executável do app
# Requer: ps2exe (instalar: Install-Module ps2exe)

$scriptContent = @'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Caminhos do Chrome
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$chromePath86 = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
$url = "https://www.absenteismocontroller.com.br/landing"

# Tenta abrir no Chrome em modo app
if (Test-Path $chromePath) {
    Start-Process $chromePath -ArgumentList "--app=$url", "--new-window"
} elseif (Test-Path $chromePath86) {
    Start-Process $chromePath86 -ArgumentList "--app=$url", "--new-window"
} else {
    # Abre no navegador padrão
    Start-Process $url
}
'@

# Salvar script temporário
$tempScript = "$env:TEMP\absenteismo_app.ps1"
$scriptContent | Out-File -FilePath $tempScript -Encoding UTF8

# Converter para executável (requer ps2exe)
# ps2exe -inputFile $tempScript -outputFile "AbsenteismoController.exe" -icon "icon.ico" -title "AbsenteismoController"

Write-Host "Script criado em: $tempScript"
Write-Host "Para criar executável, instale ps2exe: Install-Module ps2exe"
Write-Host "Depois execute: ps2exe -inputFile $tempScript -outputFile AbsenteismoController.exe"



