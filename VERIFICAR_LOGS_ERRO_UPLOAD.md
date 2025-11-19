# 🔍 VERIFICAR LOGS - ERRO NO UPLOAD

## ✅ PROGRESSO

Agora o erro está sendo retornado como JSON corretamente! A mensagem atual é:
**"Erro interno no servidor. Verifique os logs para mais detalhes."**

Isso significa que o exception handler está funcionando, mas precisamos ver os logs para identificar a causa real.

---

## 📋 VERIFICAR LOGS DO SERVIDOR

Execute no terminal SSH da Hostinger:

```bash
cd /var/www/absenteismo

# Ver últimos 100 erros
tail -100 logs/errors.log

# OU ver apenas erros relacionados a upload
tail -200 logs/errors.log | grep -i -A 20 "upload\|Upload\|UPLOAD\|exception\|error" | tail -100

# OU ver em tempo real (deixe aberto e tente fazer upload)
tail -f logs/errors.log
```

**📝 COPIE E ME ENVIE TODO O ERRO QUE APARECER!**

---

## 📋 VERIFICAR PERMISSÕES (CAUSA MAIS COMUM)

```bash
cd /var/www/absenteismo

# Verificar se a pasta uploads existe e tem permissão
ls -la uploads/

# Se não existir ou não tiver permissão:
mkdir -p uploads
chown -R www-data:www-data uploads
chmod -R 755 uploads

# Testar se consegue escrever
touch uploads/test.txt && rm uploads/test.txt && echo "✅ Permissão OK" || echo "❌ Erro de permissão"
```

---

## 📋 VERIFICAR BANCO DE DADOS

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
    import traceback
    traceback.print_exc()
"
```

---

## 📤 ENVIAR ARQUIVO CORRIGIDO

Execute no PowerShell:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
scp backend/main.py root@72.60.166.55:/var/www/absenteismo/backend/main.py
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

Após enviar o arquivo corrigido, a mensagem de erro será mais específica:
- "Erro de permissão..." se for problema de permissão
- "Erro no banco de dados..." se for problema no banco
- "Erro ao processar planilha..." se for problema com Excel
- etc.

---

## 💡 PRÓXIMOS PASSOS

1. ✅ **Execute o comando para ver os logs** (mais importante!)
2. ✅ Me envie o erro completo dos logs
3. ✅ Verifique permissões da pasta `uploads/`
4. ✅ Envie o arquivo corrigido
5. ✅ Teste novamente

**Os logs vão mostrar exatamente qual é o problema!**


