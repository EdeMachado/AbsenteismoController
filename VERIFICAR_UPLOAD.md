# ✅ VERIFICAR SE O ARQUIVO FOI ENVIADO

## 🔍 OPÇÃO 1: Verificar no Servidor (SSH)

Entre no terminal SSH da Hostinger e execute:

```bash
cd /var/www/absenteismo/backend
ls -lh main.py
```

**Se aparecer o arquivo com data/hora recente, foi enviado! ✅**

---

## 🔍 OPÇÃO 2: Tentar Enviar Novamente

Se não funcionou, execute no PowerShell:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
scp backend/main.py root@72.60.166.55:/var/www/absenteismo/backend/main.py
```

**Ele vai perguntar:**
- Se o arquivo já existe, digite `yes` para substituir
- Senha: (digite a senha do servidor)

---

## 🔄 DEPOIS DE ENVIAR - REINICIAR SERVIÇO

No terminal SSH da Hostinger:

```bash
cd /var/www/absenteismo
source venv/bin/activate

# Ver processos Gunicorn
ps aux | grep gunicorn

# Reiniciar (substitua PID pelo número do processo)
kill -HUP $(pgrep -f gunicorn)

# OU se preferir, mate e inicie novamente:
pkill gunicorn
cd /var/www/absenteismo
source venv/bin/activate
gunicorn -c gunicorn_config.py backend.main:app --daemon
```

---

## ✅ TESTAR

Acesse: https://www.absenteismocontroller.com.br/api/health

Se retornar `{"status": "ok"}`, está funcionando!

---

## 📋 RESUMO

1. ✅ Enviar arquivo: `scp backend/main.py root@72.60.166.55:/var/www/absenteismo/backend/main.py`
2. ✅ Reiniciar Gunicorn no servidor
3. ✅ Testar: https://www.absenteismocontroller.com.br/api/health


