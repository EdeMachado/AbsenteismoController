# 🚀 Como Executar o Deploy

## ✅ Script Criado: `deploy.sh`

Este script automatiza todo o processo de deploy:
1. ✅ Verifica alterações
2. ✅ Faz commit das correções
3. ✅ Faz push para GitHub
4. ✅ Conecta ao servidor e faz pull

---

## 📋 COMO EXECUTAR:

### **OPÇÃO 1: Git Bash** (Recomendado)

1. **Abra o Git Bash**
   - Clique com botão direito na pasta do projeto
   - Escolha "Git Bash Here"
   - OU abra Git Bash e navegue até:
     ```bash
     cd "/c/Users/Ede Machado/AbsenteismoConverplast"
     ```

2. **Dê permissão de execução** (se necessário):
   ```bash
   chmod +x deploy.sh
   ```

3. **Execute o script**:
   ```bash
   ./deploy.sh
   ```

4. **Siga as instruções**:
   - O script vai fazer commit e push automaticamente
   - Quando perguntar, digite "s" para fazer deploy no servidor
   - Digite seu usuário SSH quando solicitado
   - Digite a senha SSH quando solicitado

---

### **OPÇÃO 2: WSL (Windows Subsystem for Linux)**

Se você tem WSL instalado:

1. **Abra o WSL**:
   ```bash
   wsl
   ```

2. **Navegue até o projeto**:
   ```bash
   cd /mnt/c/Users/"Ede Machado"/AbsenteismoConverplast
   ```

3. **Execute o script**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

---

### **OPÇÃO 3: Manual (Passo a Passo)**

Se preferir fazer manualmente:

#### 1. Commit e Push:
```bash
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
git add frontend/static/js/produtividade.js frontend/dados_powerbi.html frontend/static/js/dados_powerbi.js
git commit -m "Correção: Edição produtividade + Filtro ordenação em Meus Dados"
git push origin main
```

#### 2. Deploy no Servidor:
```bash
ssh -p 65002 SEU_USUARIO@72.60.166.55
cd ~/domains/absenteismocontroller.com.br/public_html/absenteismo
git pull origin main
exit
```

---

## 📝 O QUE O SCRIPT FAZ:

✅ **Commit automático** das seguintes correções:
- `frontend/static/js/produtividade.js` - Correção da edição (client_id)
- `frontend/dados_powerbi.html` - Adição do filtro de ordenação
- `frontend/static/js/dados_powerbi.js` - Lógica de ordenação

✅ **Push para GitHub** automaticamente

✅ **Deploy no servidor** via SSH (opcional)

---

## ⚠️ IMPORTANTE:

- Você precisará da **senha SSH** do servidor
- O script vai perguntar se deseja fazer deploy (digite "s" para sim)
- Se o caminho do servidor for diferente, o script permite alterar

---

## 🆘 PROBLEMAS?

**Erro: "permission denied"**
```bash
chmod +x deploy.sh
```

**Erro: "bash: deploy.sh: command not found"**
- Certifique-se de estar no diretório correto
- Use: `./deploy.sh` (com o ponto e barra)

**Erro no SSH:**
- Verifique se o usuário SSH está correto
- Verifique se a porta 65002 está correta
- Tente fazer o deploy manualmente (Opção 3)

---

## ✅ APÓS O DEPLOY:

1. Acesse: **https://www.absenteismocontroller.com.br**
2. Teste a **edição no módulo Produtividade** - deve funcionar agora!
3. Teste o **filtro de ordenação no módulo Meus Dados** - deve aparecer na toolbar!

---

**Boa sorte com o deploy! 🚀**

