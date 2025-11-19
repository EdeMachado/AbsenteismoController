# 📱 PASSOS PARA ATIVAR O APP DESKTOP

## ✅ O QUE JÁ ESTÁ PRONTO:

1. ✅ Página de download criada (`/download_app`)
2. ✅ Rota de download no backend
3. ✅ Link no menu adicionado
4. ✅ App Electron configurado

---

## 🚀 O QUE VOCÊ PRECISA FAZER AGORA:

### PASSO 1: Enviar arquivos para o servidor

No PowerShell local, execute:

```powershell
# Enviar página de download
scp frontend/download_app.html root@72.60.166.55:/var/www/absenteismo/frontend/

# Enviar atualizações do menu
scp frontend/index.html root@72.60.166.55:/var/www/absenteismo/frontend/
scp frontend/configuracoes.html root@72.60.166.55:/var/www/absenteismo/frontend/

# Enviar atualizações do backend
scp backend/main.py root@72.60.166.55:/var/www/absenteismo/backend/
```

### PASSO 2: Enviar pasta do app (opcional - para download funcionar)

```powershell
# Enviar toda a pasta app-desktop
scp -r app-desktop root@72.60.166.55:/var/www/absenteismo/
```

### PASSO 3: Reiniciar o sistema no servidor

No terminal da Hostinger:

```bash
# Encontrar processo do Gunicorn
ps aux | grep gunicorn | grep -v grep

# Reiniciar (substitua PID pelo número encontrado)
kill -HUP PID
```

OU simplesmente:

```bash
# Recarregar Nginx (pode ajudar)
systemctl reload nginx
```

---

## 🎯 TESTAR:

1. Acesse: https://www.absenteismocontroller.com.br
2. Faça login
3. Clique em "📱 Baixar App" no menu
4. Veja se a página carrega
5. Clique em "Baixar App Desktop"
6. Veja se o download funciona

---

## 📝 OBSERVAÇÕES:

### Se o download não funcionar:

O download do app só funcionará se:
- A pasta `app-desktop/` estiver no servidor
- OU você compilar o app localmente e enviar o executável

### Opção mais simples (recomendada):

Por enquanto, você pode:
1. Compilar o app localmente (se tiver Node.js)
2. Criar um link direto para o arquivo compilado
3. OU simplesmente orientar os usuários a usar o `ABRIR_APP_DESKTOP.bat`

---

## 🎨 PRÓXIMOS PASSOS (OPCIONAL):

1. **Criar ícone do app:**
   - Criar `app-desktop/assets/icon.png`
   - Ícone azul 256x256

2. **Compilar o app:**
   - Instalar Node.js
   - Executar `INSTALADOR.bat`
   - O executável estará em `app-desktop/dist/`

3. **Fazer upload do executável:**
   - Enviar para o servidor
   - Criar link direto de download

---

## ✅ RESUMO RÁPIDO:

**AGORA:**
1. Envie os arquivos (PASSO 1)
2. Reinicie o sistema (PASSO 3)
3. Teste (PASSO 4)

**DEPOIS (quando quiser):**
- Compile o app localmente
- Faça upload do executável
- Ou use o `ABRIR_APP_DESKTOP.bat` que já funciona

---

## 🆘 SE TIVER DÚVIDAS:

Me diga qual passo você está e eu ajudo! 😊



