# 📤 ENVIAR backend/main.py PARA SERVIDOR

## 🚀 OPÇÃO 1: Usando IP Direto (Mais Confiável)

Execute no PowerShell:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
scp backend/main.py root@72.60.166.55:/var/www/absenteismo/backend/main.py
```

---

## 🌐 OPÇÃO 2: Usando Hostname Hostinger

Se você tem o hostname correto da Hostinger, substitua:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
scp -P 65002 backend/main.py usuario@ssh.hostinger.com:/var/www/absenteismo/backend/main.py
```

**Substitua:**
- `usuario` pelo seu usuário SSH da Hostinger
- `ssh.hostinger.com` pelo hostname correto do seu painel

---

## ✅ DEPOIS DE ENVIAR

No terminal SSH da Hostinger, execute:

```bash
cd /var/www/absenteismo
source venv/bin/activate
# Reinicia o Gunicorn
pkill -HUP gunicorn
# OU se estiver rodando como serviço:
systemctl restart absenteismo
```

---

## 🔍 VERIFICAR SE FUNCIONOU

Acesse: https://www.absenteismocontroller.com.br/api/health

Se retornar `{"status": "ok"}`, está funcionando!


