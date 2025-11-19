# 🚀 CRIAR APP EXECUTÁVEL COM ÍCONE

## Opção 1: Usar AutoIt (Recomendado - Mais Fácil)

### Passo 1: Baixar AutoIt
- Baixe em: https://www.autoitscript.com/site/autoit/downloads/
- Instale o AutoIt

### Passo 2: Criar Script

Crie um arquivo `AbsenteismoController.au3`:

```autoit
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
```

### Passo 3: Compilar

1. Clique com botão direito no arquivo `.au3`
2. Selecione "Compile Script"
3. Será criado um `.exe` com ícone padrão

### Passo 4: Adicionar Ícone Personalizado

1. Baixe ou crie um ícone `.ico` (256x256)
2. Use o AutoIt Compiler com opção de ícone
3. OU use Resource Hacker para trocar o ícone depois

---

## Opção 2: Usar PyInstaller (Se tiver Python)

### Passo 1: Instalar PyInstaller

```bash
pip install pyinstaller
```

### Passo 2: Criar Script Python

Crie `app.py`:

```python
import subprocess
import os
import sys

chrome_paths = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
]

url = "https://www.absenteismocontroller.com.br/landing"

for chrome_path in chrome_paths:
    if os.path.exists(chrome_path):
        subprocess.Popen([chrome_path, f"--app={url}", "--new-window"])
        sys.exit(0)

# Se Chrome não encontrado, abre no navegador padrão
os.startfile(url)
```

### Passo 3: Compilar

```bash
pyinstaller --onefile --windowed --icon=icon.ico --name="AbsenteismoController" app.py
```

---

## Opção 3: Usar Batch to Exe Converter (Mais Simples)

### Passo 1: Baixar
- Baixe: http://www.battoexeconverter.com/
- É gratuito e simples

### Passo 2: Converter
1. Abra o programa
2. Selecione o arquivo `ABRIR_APP_DESKTOP.bat`
3. Configure:
   - Nome: AbsenteismoController
   - Ícone: Selecione um arquivo .ico
   - Modo: Invisible (sem janela)
4. Clique em "Compile"
5. Pronto! Terá um .exe

---

## 🎨 Criar Ícone

1. Use um gerador online: https://www.favicon-generator.org/
2. Ou use o logo do sistema
3. Salve como `.ico` (256x256)

---

## ✅ Recomendação

**Use a Opção 3 (Batch to Exe Converter)** - É a mais simples e rápida!



