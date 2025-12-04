# 🚀 PASSO A PASSO - Deploy da Correção

## ✅ O QUE JÁ FOI FEITO:
- ✅ Correção do gráfico aplicada
- ✅ Commit realizado (50462a2)
- ✅ Push para GitHub concluído

---

## 📋 AGORA VAMOS FAZER O DEPLOY:

### **OPÇÃO 1: Via PowerShell (Do seu computador)** ⭐ RECOMENDADO

#### Passo 1: Abrir PowerShell
1. Pressione `Win + X`
2. Escolha **"Windows PowerShell"** ou **"Terminal"**
3. Navegue até a pasta do projeto:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
```

#### Passo 2: Executar o comando SSH
Copie e cole este comando (vou ajustar quando você me passar o usuário SSH):

```powershell
ssh -p 65002 SEU_USUARIO@72.60.166.55
```

**Quando pedir a senha, digite a senha SSH do servidor.**

#### Passo 3: Após conectar, execute:
```bash
cd ~/domains/absenteismocontroller.com.br/public_html/absenteismo
git pull origin main
```

**OU se esse caminho não funcionar, tente:**
```bash
cd ~/public_html/absenteismo
git pull origin main
```

#### Passo 4: Sair do SSH
```bash
exit
```

---

### **OPÇÃO 2: Via Terminal da Hostinger** (hPanel)

#### Passo 1: Acessar o Terminal
1. Acesse o **hPanel** da Hostinger
2. Vá em **Avançado** → **Terminal**
3. Clique em **"Abrir Terminal"**

#### Passo 2: Navegar até o sistema
```bash
cd ~/domains/absenteismocontroller.com.br/public_html/absenteismo
```

**OU:**
```bash
cd ~/public_html/absenteismo
```

#### Passo 3: Fazer pull
```bash
git pull origin main
```

---

## ❓ QUAL CAMINHO USAR?

Para descobrir o caminho correto, no terminal execute:
```bash
pwd
ls -la
```

Procure pela pasta `absenteismo` ou arquivos como `backend`, `frontend`.

---

## ✅ VERIFICAÇÃO

Após o deploy, acesse:
1. **https://www.absenteismocontroller.com.br**
2. Faça login
3. Vá para **Dashboard**
4. Role até **"Top CIDs por Setor"**
5. Deve aparecer um **gráfico de barras horizontal** 🎉

---

## 🆘 SE DER ERRO

**Erro: "git pull" não funciona**
- Verifique se está no diretório certo: `pwd`
- Verifique se tem arquivos: `ls -la`
- Talvez precise fazer: `git status` primeiro

**Erro: Caminho não encontrado**
- Execute: `find ~ -name "absenteismo" -type d 2>/dev/null`
- Ou me diga qual caminho aparece quando você faz `ls` na home

---

## 📞 VAMOS FAZER JUNTOS!

**Me diga:**
1. Qual opção você prefere? (PowerShell ou Terminal Hostinger)
2. Qual é o seu **usuário SSH**? (para eu criar o comando completo)
3. Se já tentou, o que apareceu?



