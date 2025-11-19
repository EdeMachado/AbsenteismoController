#RequireAdmin
#NoTrayIcon

; Caminhos do Chrome
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$chromePath86 = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
$url = "https://www.absenteismocontroller.com.br/landing"

; Tenta abrir no Chrome em modo app
If FileExists($chromePath) Then
    Run($chromePath & ' --app=' & $url & ' --new-window')
ElseIf FileExists($chromePath86) Then
    Run($chromePath86 & ' --app=' & $url & ' --new-window')
Else
    ; Abre no navegador padrão
    Run("rundll32.exe url.dll,FileProtocolHandler " & $url)
EndIf



