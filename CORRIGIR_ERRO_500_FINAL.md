# 🔧 CORREÇÃO FINAL - ERRO 500 NO UPLOAD

## ✅ CORREÇÃO APLICADA

Adicionado **exception handler global** no FastAPI para garantir que **TODOS** os erros sejam retornados como JSON, não como texto.

### O que foi corrigido:
1. ✅ Exception handler global adicionado
2. ✅ Todos os erros agora retornam JSON com `{"detail": "mensagem"}`
3. ✅ Logs detalhados de erros não tratados
4. ✅ Frontend melhorado para ler resposta de erro

---

## 📤 ENVIAR ARQUIVO CORRIGIDO

Execute no PowerShell:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"

# Enviar backend
scp backend/main.py root@72.60.166.55:/var/www/absenteismo/backend/main.py

# Enviar frontend
scp frontend/static/js/upload.js root@72.60.166.55:/var/www/absenteismo/frontend/static/js/upload.js
```

---

## 🔄 REINICIAR SERVIÇO

No terminal SSH da Hostinger:

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

## ✅ TESTAR

1. **Limpe o cache do navegador** (Ctrl+Shift+Delete ou Ctrl+F5)
2. **Abra o console** (F12)
3. **Tente fazer upload**
4. **Agora você verá a mensagem de erro detalhada!**

---

## 🔍 SE AINDA DER ERRO

Agora a mensagem de erro será exibida corretamente no console e no alerta.

**Verifique:**
- Console do navegador (F12) - verá a mensagem completa
- Alerta no navegador - mostrará a mensagem de erro
- Logs do servidor - para mais detalhes técnicos

---

## 📋 VERIFICAR LOGS (se necessário)

```bash
cd /var/www/absenteismo
tail -50 logs/errors.log
```

---

## 💡 O QUE MUDOU

**Antes:**
- Erro retornava apenas "Internal Server Error" como texto
- Frontend não conseguia ler a mensagem de erro

**Agora:**
- Erro retorna JSON: `{"detail": "mensagem detalhada"}`
- Frontend consegue ler e exibir a mensagem
- Exception handler global captura todos os erros

---

✅ **Teste novamente após enviar os arquivos!**


