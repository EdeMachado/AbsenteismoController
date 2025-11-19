# 🚀 CRIAR APP EXECUTÁVEL - GUIA RÁPIDO

## ✅ SOLUÇÃO MAIS SIMPLES: Batch to Exe Converter

### Passo 1: Baixar o Programa
- Site: http://www.battoexeconverter.com/
- É gratuito e funciona offline
- Baixe e instale

### Passo 2: Converter o .bat para .exe

1. Abra o "Batch to Exe Converter"
2. Clique em "Browse" e selecione: `ABRIR_APP_DESKTOP.bat`
3. Configure:
   - **Version Information:**
     - File Description: `AbsenteismoController`
     - Product Name: `AbsenteismoController`
     - Company Name: `GrupoBiomed`
   - **Options:**
     - ✅ Invisible application (sem janela)
     - ✅ Run as administrator (se necessário)
   - **Icon:**
     - Clique em "..." e selecione um arquivo `.ico`
     - (Você pode criar um ícone azul simples)
4. Clique em "Compile"
5. Salve como: `AbsenteismoController.exe`

### Passo 3: Testar
- Clique duas vezes no `.exe`
- Deve abrir direto, sem perguntar nada
- Com o ícone e nome que você configurou

---

## 🎨 CRIAR ÍCONE SIMPLES

### Opção 1: Online (Mais Fácil)
1. Acesse: https://www.favicon-generator.org/
2. Faça upload de uma imagem ou use texto
3. Baixe o `.ico`

### Opção 2: Usar Logo Existente
- Se tiver um logo do sistema, converta para `.ico`
- Use: https://convertio.co/pt/png-ico/

---

## 📦 ALTERNATIVA: Usar PyInstaller (Se tiver Python)

Se você tiver Python instalado:

```bash
# Instalar PyInstaller
pip install pyinstaller

# Compilar
cd app-desktop
pyinstaller --onefile --windowed --icon=icon.ico --name="AbsenteismoController" app.py
```

O executável estará em `app-desktop/dist/AbsenteismoController.exe`

---

## ✅ RESULTADO FINAL

Você terá:
- ✅ `AbsenteismoController.exe` - Executável
- ✅ Com ícone personalizado
- ✅ Com nome "AbsenteismoController"
- ✅ Abre direto, sem perguntar
- ✅ Funciona como um app nativo

---

## 💡 RECOMENDAÇÃO

**Use o Batch to Exe Converter** - É o mais simples e não precisa de Python ou outras ferramentas!



