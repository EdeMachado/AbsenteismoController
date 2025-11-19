# 🔍 VERIFICAR ERRO 500 NO UPLOAD

## 📋 PASSO 1: Verificar Logs no Servidor

Entre no terminal SSH da Hostinger e execute:

```bash
cd /var/www/absenteismo

# Ver últimos erros
tail -50 logs/errors.log

# OU ver em tempo real
tail -f logs/errors.log
```

Depois tente fazer upload novamente e veja o erro detalhado.

---

## 📋 PASSO 2: Verificar Logs do Gunicorn

```bash
# Ver processos Gunicorn
ps aux | grep gunicorn

# Ver logs do sistema (se configurado)
journalctl -u absenteismo -n 50 --no-pager
```

---

## 📋 PASSO 3: Testar Upload Manualmente

No terminal SSH:

```bash
cd /var/www/absenteismo
source venv/bin/activate

# Testar importação do módulo
python -c "from backend.main import app; print('OK')"

# Verificar se há erros de sintaxe
python -m py_compile backend/main.py
```

---

## 🔧 CORREÇÕES APLICADAS

1. ✅ Validação de `dados_originais` (JSON)
2. ✅ Tratamento de erros de serialização
3. ✅ Mensagens de erro mais claras
4. ✅ Logs detalhados

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

## ✅ PRÓXIMOS PASSOS

1. Envie o arquivo corrigido
2. Reinicie o serviço
3. Verifique os logs
4. Tente fazer upload novamente
5. Me envie o erro que aparecer nos logs


