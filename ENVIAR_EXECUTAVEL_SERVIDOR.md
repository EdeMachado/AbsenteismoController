# 📤 ENVIAR EXECUTÁVEL PARA O SERVIDOR

## ✅ Executável criado com sucesso!

O arquivo `AbsenteismoController.exe` está em:
`app-desktop\dist\AbsenteismoController.exe`

## 🚀 Enviar para o servidor

### PASSO 1: Criar estrutura no servidor

No terminal da Hostinger:

```bash
mkdir -p /var/www/absenteismo/app-desktop/dist
```

### PASSO 2: Enviar executável

No PowerShell local:

```powershell
scp app-desktop\dist\AbsenteismoController.exe root@72.60.166.55:/var/www/absenteismo/app-desktop/dist/
```

### PASSO 3: Enviar arquivos atualizados

```powershell
# Backend atualizado
scp backend/main.py root@72.60.166.55:/var/www/absenteismo/backend/

# JavaScript atualizado
scp frontend/static/js/auth.js root@72.60.166.55:/var/www/absenteismo/frontend/static/js/
```

### PASSO 4: Reiniciar Gunicorn

No terminal da Hostinger:

```bash
ps aux | grep gunicorn | grep -v grep
# Pegue o PID e execute:
kill -HUP PID
```

---

## ✅ Pronto!

Agora quando clicar em "📱 Baixar App" no menu:
- Baixará o arquivo `AbsenteismoController.exe`
- Com ícone e nome "AbsenteismoController"
- Abre direto, sem perguntar nada
- Abre na página de login

---

## 🎯 Testar

1. Recarregue a página (Ctrl+F5)
2. Clique em "📱 Baixar App"
3. O arquivo `.exe` será baixado
4. Clique duas vezes no `.exe`
5. O app abre na página de login



