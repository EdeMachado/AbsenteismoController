# 📤 ENVIAR ARQUIVO CORRIGIDO

## ✅ Execute este comando no PowerShell:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
scp backend/logger.py root@72.60.166.55:/var/www/absenteismo/backend/logger.py
```

**Ele vai pedir a senha do servidor** - digite a senha quando solicitado.

---

## 🔄 Depois, no terminal SSH da Hostinger:

```bash
cd /var/www/absenteismo
source venv/bin/activate
kill -HUP $(pgrep -f gunicorn)
```

---

## ✅ Testar

1. Limpe o cache do navegador (Ctrl+F5)
2. Tente fazer upload novamente
3. Deve funcionar agora!

---

## 💡 Se der erro de conexão

Verifique se:
- ✅ Você está conectado à internet
- ✅ O IP do servidor está correto (72.60.166.55)
- ✅ A senha está correta


