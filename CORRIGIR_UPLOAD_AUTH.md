# 🔧 CORRIGIR ERRO 500 NO UPLOAD - AUTENTICAÇÃO

## ✅ CORREÇÃO APLICADA

O problema era que o token de autenticação não estava sendo enviado no fetch do upload.

### O que foi corrigido:
1. ✅ Adicionado token de autenticação no header do fetch
2. ✅ Melhorado tratamento de erros para mostrar mensagem detalhada
3. ✅ Logs mais detalhados no console

---

## 📤 ENVIAR ARQUIVO CORRIGIDO

Execute no PowerShell:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
scp frontend/static/js/upload.js root@72.60.166.55:/var/www/absenteismo/frontend/static/js/upload.js
```

---

## 🔄 REINICIAR SERVIÇO (se necessário)

No terminal SSH da Hostinger:

```bash
cd /var/www/absenteismo
source venv/bin/activate
kill -HUP $(pgrep -f gunicorn)
```

---

## ✅ TESTAR

1. **Limpe o cache do navegador:**
   - Pressione `Ctrl+Shift+Delete`
   - Selecione "Imagens e arquivos em cache"
   - Clique em "Limpar dados"
   - OU simplesmente pressione `Ctrl+F5` na página de upload

2. **Abra o console do navegador:**
   - Pressione `F12`
   - Vá na aba "Console"

3. **Tente fazer upload novamente**

4. **Verifique:**
   - Se aparecer erro, veja a mensagem completa no console
   - A mensagem de erro agora será mais detalhada
   - O token de autenticação será enviado corretamente

---

## 🔍 SE AINDA DER ERRO

1. **Verifique o console do navegador (F12):**
   - Veja a mensagem de erro completa
   - Copie e me envie

2. **Verifique os logs no servidor:**
   ```bash
   cd /var/www/absenteismo
   tail -50 logs/errors.log
   ```

3. **Verifique se está logado:**
   - O token deve estar em `localStorage.getItem('access_token')`
   - Se não estiver, faça login novamente

---

## 📋 RESUMO

- ✅ Token de autenticação agora é enviado
- ✅ Mensagens de erro mais detalhadas
- ✅ Logs no console para debug

**Teste novamente após enviar o arquivo!**


