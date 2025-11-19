# 🔧 CORRIGIR ERRO 500 NO UPLOAD

## ✅ CORREÇÃO APLICADA

Corrigido o tratamento de `dados_originais` no upload para garantir que:
- ✅ Valida se é JSON válido antes de salvar
- ✅ Converte dict para JSON string se necessário
- ✅ Trata erros de serialização graciosamente
- ✅ Adiciona logs detalhados para debug

---

## 📤 ENVIAR CORREÇÃO PARA SERVIDOR

Execute no PowerShell:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
scp backend/main.py root@72.60.166.55:/var/www/absenteismo/backend/main.py
```

---

## 🔄 REINICIAR SERVIÇO

No terminal SSH da Hostinger:

```bash
cd /var/www/absenteismo
source venv/bin/activate

# Reiniciar Gunicorn
kill -HUP $(pgrep -f gunicorn)

# OU se preferir:
pkill gunicorn
gunicorn -c gunicorn_config.py backend.main:app --daemon
```

---

## 🔍 VERIFICAR LOGS (se ainda der erro)

No terminal SSH:

```bash
cd /var/www/absenteismo
tail -f logs/errors.log
```

Depois tente fazer upload novamente e veja o erro detalhado.

---

## ✅ TESTAR

1. Acesse: https://www.absenteismocontroller.com.br/upload
2. Selecione um cliente
3. Faça upload de uma planilha
4. Verifique se funciona

---

## 📋 O QUE FOI CORRIGIDO

- ✅ Validação de `dados_originais` antes de salvar
- ✅ Conversão segura de dict para JSON
- ✅ Tratamento de erros de serialização
- ✅ Logs detalhados para debug


