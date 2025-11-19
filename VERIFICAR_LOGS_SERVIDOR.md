# 🔍 VERIFICAR LOGS DO SERVIDOR - ERRO 500

## 🚨 PROBLEMA

O servidor está retornando erro 500, mas a mensagem de erro detalhada não está chegando ao frontend.

---

## 📋 PASSO 1: Verificar Logs de Erro (CRÍTICO!)

Entre no terminal SSH da Hostinger e execute:

```bash
cd /var/www/absenteismo

# Ver últimos 100 erros
tail -100 logs/errors.log

# OU ver em tempo real (deixe aberto e tente fazer upload)
tail -f logs/errors.log
```

**Copie e me envie TODO o erro que aparecer!**

---

## 📋 PASSO 2: Verificar Logs do App

```bash
cd /var/www/absenteismo

# Ver logs gerais do app
tail -100 logs/app.log

# Ver logs de segurança (pode ter informações)
tail -50 logs/security.log
```

---

## 📋 PASSO 3: Verificar Permissões da Pasta Uploads

```bash
cd /var/www/absenteismo

# Verificar se a pasta existe e tem permissão
ls -la uploads/

# Se não existir ou não tiver permissão:
mkdir -p uploads
chown -R www-data:www-data uploads
chmod -R 755 uploads

# Verificar se consegue escrever
touch uploads/test.txt && rm uploads/test.txt && echo "✅ Permissão OK"
```

---

## 📋 PASSO 4: Verificar Banco de Dados

```bash
cd /var/www/absenteismo
source venv/bin/activate

# Testar conexão com banco
python -c "
from backend.database import get_db, engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ Banco de dados OK')
except Exception as e:
    print(f'❌ Erro no banco: {e}')
"
```

---

## 📋 PASSO 5: Testar Upload Manualmente (Python)

```bash
cd /var/www/absenteismo
source venv/bin/activate

# Testar se consegue importar módulos
python -c "
try:
    from backend.main import app
    from backend.excel_processor import ExcelProcessor
    from backend.models import Atestado, Upload
    print('✅ Imports OK')
except Exception as e:
    print(f'❌ Erro nos imports: {e}')
    import traceback
    traceback.print_exc()
"
```

---

## 📋 PASSO 6: Verificar Processo Gunicorn

```bash
# Ver processos Gunicorn
ps aux | grep gunicorn

# Ver se há erros no processo
# (os erros podem estar sendo redirecionados para logs)
```

---

## 📋 PASSO 7: Verificar Variáveis de Ambiente

```bash
cd /var/www/absenteismo

# Verificar .env
cat .env

# Verificar se SECRET_KEY está definida
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('SECRET_KEY:', 'OK' if os.getenv('SECRET_KEY') else 'FALTANDO')"
```

---

## 🔧 CORREÇÕES APLICADAS NO FRONTEND

1. ✅ Melhorado tratamento de erro para ler resposta do servidor
2. ✅ Logs detalhados no console do navegador
3. ✅ Tenta ler JSON e texto da resposta de erro

---

## 📤 ENVIAR ARQUIVO CORRIGIDO

Execute no PowerShell:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
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

1. **Execute o PASSO 1** (verificar logs) - **MAIS IMPORTANTE!**
2. Me envie o erro completo que aparecer nos logs
3. Verifique permissões da pasta `uploads/`
4. Envie o arquivo corrigido do frontend
5. Teste novamente

---

## 💡 DICA

O erro pode ser:
- ❌ Permissão na pasta `uploads/`
- ❌ Erro no banco de dados (tabela não existe, constraint, etc.)
- ❌ Erro ao processar Excel (pandas, openpyxl)
- ❌ Erro ao serializar JSON (`dados_originais`)
- ❌ Cliente não encontrado
- ❌ Erro de autenticação/autorização

**Os logs vão mostrar exatamente qual é!**

---

## 📝 COMANDO RÁPIDO PARA VER LOGS

```bash
cd /var/www/absenteismo && tail -100 logs/errors.log | grep -A 20 "upload\|Upload\|UPLOAD" || tail -50 logs/errors.log
```

Este comando mostra os últimos erros relacionados a upload.


