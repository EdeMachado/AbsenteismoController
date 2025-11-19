# 🔧 SOLUÇÃO ERRO 500 NO UPLOAD

## 🚨 PROBLEMA

O servidor está retornando erro 500, mas a mensagem detalhada não está chegando ao frontend.

---

## 📋 PASSO 1: VERIFICAR LOGS (MAIS IMPORTANTE!)

Execute no terminal SSH da Hostinger:

```bash
cd /var/www/absenteismo

# Ver últimos erros relacionados a upload
tail -100 logs/errors.log | grep -i -A 15 "upload\|Upload\|UPLOAD" | tail -50

# OU ver todos os últimos erros
tail -50 logs/errors.log

# OU ver em tempo real (deixe aberto e tente fazer upload)
tail -f logs/errors.log
```

**📝 COPIE E ME ENVIE TODO O ERRO QUE APARECER!**

---

## 📋 PASSO 2: VERIFICAR PERMISSÕES

```bash
cd /var/www/absenteismo

# Verificar se a pasta uploads existe
ls -la uploads/

# Se não existir ou não tiver permissão:
mkdir -p uploads
chown -R www-data:www-data uploads
chmod -R 755 uploads

# Testar se consegue escrever
touch uploads/test.txt && rm uploads/test.txt && echo "✅ Permissão OK" || echo "❌ Erro de permissão"
```

---

## 📋 PASSO 3: VERIFICAR BANCO DE DADOS

```bash
cd /var/www/absenteismo
source venv/bin/activate

# Testar conexão
python -c "
from backend.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
        print('✅ Banco OK')
except Exception as e:
    print(f'❌ Erro: {e}')
"
```

---

## 📋 PASSO 4: TESTAR IMPORTS

```bash
cd /var/www/absenteismo
source venv/bin/activate

python -c "
try:
    from backend.main import app
    from backend.excel_processor import ExcelProcessor
    from backend.models import Atestado, Upload, Client
    print('✅ Imports OK')
except Exception as e:
    print(f'❌ Erro: {e}')
    import traceback
    traceback.print_exc()
"
```

---

## 📤 ENVIAR ARQUIVOS CORRIGIDOS

Execute no PowerShell:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"

# Enviar frontend
scp frontend/static/js/upload.js root@72.60.166.55:/var/www/absenteismo/frontend/static/js/upload.js

# Enviar script de verificação
scp verificar_logs_upload.sh root@72.60.166.55:/var/www/absenteismo/
```

---

## 🔄 REINICIAR SERVIÇO

```bash
cd /var/www/absenteismo
source venv/bin/activate
kill -HUP $(pgrep -f gunicorn)
```

---

## ✅ TESTAR NOVAMENTE

1. **Limpe o cache do navegador** (Ctrl+Shift+Delete)
2. **Abra o console** (F12)
3. **Tente fazer upload**
4. **Veja a mensagem de erro no console**

---

## 🔍 COMANDO RÁPIDO PARA VER LOGS

```bash
cd /var/www/absenteismo && tail -100 logs/errors.log | grep -i -A 20 "upload\|error\|exception\|traceback" | head -100
```

---

## 💡 POSSÍVEIS CAUSAS

1. ❌ **Permissão na pasta `uploads/`** - Mais comum!
2. ❌ **Erro no banco de dados** (tabela não existe, constraint)
3. ❌ **Erro ao processar Excel** (pandas, openpyxl)
4. ❌ **Erro ao serializar JSON** (`dados_originais`)
5. ❌ **Cliente não encontrado**
6. ❌ **Erro de autenticação**

**Os logs vão mostrar exatamente qual é!**

---

## 📝 PRÓXIMOS PASSOS

1. ✅ Execute o **PASSO 1** (verificar logs)
2. ✅ Me envie o erro completo dos logs
3. ✅ Verifique permissões (PASSO 2)
4. ✅ Envie os arquivos corrigidos
5. ✅ Teste novamente

**Sem os logs, não consigo identificar a causa exata do erro!**


