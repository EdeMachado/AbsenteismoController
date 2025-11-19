# 📤 ENVIAR CORREÇÕES PARA UPLOAD

## ✅ Execute estes comandos no PowerShell:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"

# Enviar logger.py (corrigido)
scp backend/logger.py root@72.60.166.55:/var/www/absenteismo/backend/logger.py

# Enviar main.py (corrigido - remove filename do context)
scp backend/main.py root@72.60.166.55:/var/www/absenteismo/backend/main.py
```

**Ele vai pedir a senha do servidor** - digite quando solicitado.

---

## 🔄 Depois, no terminal SSH da Hostinger:

```bash
cd /var/www/absenteismo
source venv/bin/activate

# Reiniciar Gunicorn
kill -HUP $(pgrep -f gunicorn)

# OU se preferir, reiniciar completamente:
pkill gunicorn
gunicorn -c gunicorn_config.py backend.main:app --daemon
```

---

## ✅ Testar

1. **Limpe o cache do navegador** (Ctrl+Shift+Delete ou Ctrl+F5)
2. **Tente fazer upload novamente**
3. **Agora deve funcionar!**

---

## 🔍 O que foi corrigido:

1. ✅ `logger.py` - Filtra campos reservados do LogRecord
2. ✅ `main.py` - Muda `filename` para `file_name` no context do log_error

---

## 💡 Se ainda der erro:

Verifique os logs novamente:
```bash
tail -50 /var/www/absenteismo/logs/errors.log
```

E me envie o erro completo.


