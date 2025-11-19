# 🗑️ REMOVER BOTÕES - PASSO A PASSO

## ✅ Arquivos já atualizados localmente:
- ✅ `frontend/index.html` - Botão "Baixar App" removido
- ✅ `frontend/configuracoes.html` - Botão "Baixar App" removido  
- ✅ `frontend/clientes.html` - Botões "Baixar App" e "Dashboard" removidos

## 📤 ENVIAR PARA O SERVIDOR:

### No PowerShell local, execute:

```powershell
scp frontend/index.html root@72.60.166.55:/var/www/absenteismo/frontend/
scp frontend/configuracoes.html root@72.60.166.55:/var/www/absenteismo/frontend/
scp frontend/clientes.html root@72.60.166.55:/var/www/absenteismo/frontend/
```

### Depois, no terminal da Hostinger:

```bash
# Reiniciar Gunicorn
ps aux | grep gunicorn | grep -v grep
kill -HUP PID
```

## 🔄 LIMPAR CACHE DO NAVEGADOR:

1. Pressione **Ctrl+Shift+Delete**
2. Selecione "Imagens e arquivos em cache"
3. Clique em "Limpar dados"
4. OU simplesmente pressione **Ctrl+F5** na página

## ✅ TESTAR:

1. Recarregue a página com **Ctrl+F5**
2. Verifique se os botões sumiram
3. Se ainda aparecerem, limpe o cache completamente

---

Execute os comandos acima e limpe o cache do navegador!



