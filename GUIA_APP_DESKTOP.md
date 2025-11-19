# 📱 App Desktop - AbsenteismoController

## 🎯 Duas Opções Disponíveis

### ✅ Opção 1: App Simples (Recomendado - Sem instalação)

**Arquivo:** `ABRIR_APP_DESKTOP.bat`

- ✅ Não precisa instalar nada
- ✅ Funciona imediatamente
- ✅ Abre o Chrome em modo app (sem barra de endereço)
- ✅ Parece um app nativo

**Como usar:**
1. Clique duas vezes em `ABRIR_APP_DESKTOP.bat`
2. O app abre automaticamente

---

### ✅ Opção 2: App Electron (App completo)

**Pasta:** `app-desktop/`

- ✅ App nativo do Windows
- ✅ Instalável (cria atalho no menu)
- ✅ Mais recursos (menu, atalhos)
- ✅ Requer Node.js para compilar

**Como instalar:**

1. **Instalar Node.js** (se não tiver):
   - Baixe em: https://nodejs.org/
   - Instale a versão LTS

2. **Instalar dependências:**
   ```bash
   cd app-desktop
   npm install
   ```

3. **Compilar:**
   ```bash
   npm run build-win
   ```
   
   OU simplesmente execute:
   ```bash
   INSTALAR_APP.bat
   ```

4. **Instalar:**
   - Vá em `app-desktop/dist/`
   - Execute o instalador `.exe`
   - Siga o assistente de instalação

---

## 🚀 Recomendação

**Use a Opção 1** (`ABRIR_APP_DESKTOP.bat`) se:
- Quer algo rápido e simples
- Não quer instalar Node.js
- Quer usar imediatamente

**Use a Opção 2** (Electron) se:
- Quer um app instalado no sistema
- Quer atalhos no menu Iniciar
- Quer um app mais "profissional"

---

## 📋 Comparação

| Recurso | Opção 1 (Batch) | Opção 2 (Electron) |
|---------|----------------|-------------------|
| Instalação | ❌ Não precisa | ✅ Sim |
| Compilação | ❌ Não precisa | ✅ Sim |
| Atalho no menu | ❌ Não | ✅ Sim |
| Menu do app | ❌ Não | ✅ Sim |
| Velocidade | ⚡ Instantâneo | ⚡ Rápido |
| Tamanho | 📦 Mínimo | 📦 ~100MB |

---

## 🎨 Personalização

### Alterar URL (Opção 1)

Edite `ABRIR_APP_DESKTOP.bat` e altere:
```batch
start "" %CHROME_PATH% --app=https://www.absenteismocontroller.com.br
```

### Alterar URL (Opção 2)

Edite `app-desktop/main.js` e altere:
```javascript
const PRODUCTION_URL = 'https://www.absenteismocontroller.com.br';
```

---

## 🐛 Solução de Problemas

### Opção 1 não funciona
- Verifique se o Chrome está instalado
- Se não tiver Chrome, o script abre no navegador padrão

### Opção 2 não compila
- Verifique se Node.js está instalado: `node --version`
- Execute `npm install` novamente
- Verifique se tem espaço em disco

---

## ✅ Pronto!

Agora você tem um app desktop para o sistema! 🎉



