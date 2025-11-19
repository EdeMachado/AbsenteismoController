# 🔧 CORRIGIR ERRO 500 - Download App

## Problema
A página `/download_app` retorna erro 500 porque o arquivo não está no servidor.

## Solução

### PASSO 1: Enviar arquivo para o servidor

No PowerShell local:

```powershell
scp frontend/download_app.html root@72.60.166.55:/var/www/absenteismo/frontend/
```

### PASSO 2: Verificar se o arquivo foi enviado

No terminal da Hostinger:

```bash
# Verificar se o arquivo existe
ls -lh /var/www/absenteismo/frontend/download_app.html

# Verificar permissões
chmod 644 /var/www/absenteismo/frontend/download_app.html
```

### PASSO 3: Reiniciar Gunicorn

```bash
cd /var/www/absenteismo
source venv/bin/activate

# Encontrar PID
ps aux | grep gunicorn | grep -v grep

# Reiniciar (substitua PID)
kill -HUP PID
```

### PASSO 4: Verificar logs (se ainda der erro)

```bash
# Ver últimos erros
tail -50 /var/www/absenteismo/logs/app.log
tail -50 /var/www/absenteismo/logs/errors.log
```

---

## Testar

1. Recarregue a página: https://www.absenteismocontroller.com.br/download_app
2. Ou acesse pelo botão "Baixar App" no menu



