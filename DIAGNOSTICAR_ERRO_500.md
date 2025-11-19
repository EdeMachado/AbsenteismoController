# 🔍 DIAGNOSTICAR ERRO 500 NO UPLOAD

## 🚨 PROBLEMA

O upload está retornando erro 500 (Internal Server Error) sem mostrar a mensagem detalhada.

---

## 📋 PASSO 1: Verificar Logs no Servidor (IMPORTANTE!)

Entre no terminal SSH da Hostinger e execute:

```bash
cd /var/www/absenteismo

# Ver últimos 100 erros
tail -100 logs/errors.log

# OU ver em tempo real (deixe aberto e tente fazer upload)
tail -f logs/errors.log
```

**Copie e me envie o erro completo que aparecer!**

---

## 📋 PASSO 2: Verificar Logs do Gunicorn

```bash
# Ver processos Gunicorn
ps aux | grep gunicorn

# Ver se há erros no stdout/stderr do Gunicorn
# (os erros podem estar sendo redirecionados)
```

---

## 📋 PASSO 3: Verificar Permissões

```bash
cd /var/www/absenteismo

# Verificar permissões da pasta uploads
ls -la uploads/

# Se não existir ou não tiver permissão, criar:
mkdir -p uploads
chown -R www-data:www-data uploads
chmod -R 755 uploads
```

---

## 📋 PASSO 4: Testar Upload Manualmente (Python)

No terminal SSH:

```bash
cd /var/www/absenteismo
source venv/bin/activate

# Testar se consegue importar
python -c "from backend.main import app; print('✅ Import OK')"

# Verificar se há erros de sintaxe
python -m py_compile backend/main.py && echo "✅ Sintaxe OK"
```

---

## 📋 PASSO 5: Verificar Banco de Dados

```bash
cd /var/www/absenteismo
source venv/bin/activate

# Testar conexão com banco
python -c "from backend.database import get_db; db = next(get_db()); print('✅ Banco OK')"
```

---

## 🔧 CORREÇÕES APLICADAS

1. ✅ Frontend agora mostra mensagem de erro detalhada
2. ✅ Backend retorna mensagens mais específicas
3. ✅ Logs detalhados no servidor

---

## 📤 ENVIAR ARQUIVOS CORRIGIDOS

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

```bash
cd /var/www/absenteismo
source venv/bin/activate
kill -HUP $(pgrep -f gunicorn)
```

---

## ✅ PRÓXIMOS PASSOS

1. **Execute o PASSO 1** (verificar logs) e me envie o erro completo
2. Verifique permissões da pasta `uploads/`
3. Teste novamente após enviar os arquivos corrigidos
4. Se ainda der erro, me envie:
   - Erro completo dos logs
   - Mensagem que aparece no navegador (agora será mais detalhada)

---

## 💡 DICA

O erro pode ser:
- ❌ Permissão na pasta `uploads/`
- ❌ Erro no banco de dados
- ❌ Erro ao processar Excel (pandas)
- ❌ Erro ao serializar JSON
- ❌ Cliente não encontrado

**Os logs vão mostrar exatamente qual é!**


