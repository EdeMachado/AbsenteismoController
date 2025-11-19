# 🚀 Comandos Deploy - Sequência Completa

## 📋 PASSO 1: Verificar Arquivos Localmente

**Execute no PowerShell do seu computador:**

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
dir
```

**📤 Me envie o resultado**

---

## 🔐 PASSO 2: Acessar SSH da Hostinger

**No hPanel da Hostinger:**
1. Vá em **Avançado** → **SSH**
2. Anote as credenciais:
   - Host/Server: _______________
   - Porta: _______________
   - Usuário: _______________
   - Senha: _______________

**No PowerShell do seu computador:**

```powershell
ssh usuario@ssh.hostinger.com -p 65002
```

*(Substitua pelos dados reais do hPanel)*

**📤 Me diga:**
- ✅ Conseguiu conectar?
- Qual mensagem apareceu?

---

## 🔍 PASSO 3: Verificar Ambiente no Servidor

**No terminal SSH, execute:**

```bash
python3 --version
```

**📤 Me envie o resultado**

```bash
pwd
whoami
```

**📤 Me envie o resultado**

```bash
df -h
```

**📤 Me envie o resultado**

---

## 📁 PASSO 4: Navegar para Diretório do Site

**Execute:**

```bash
cd ~/domains/absenteismocontroller.com.br/public_html
```

**OU se não existir:**

```bash
cd ~/public_html
```

**📤 Me diga qual caminho funcionou**

```bash
pwd
```

**📤 Me envie o resultado**

---

## 📁 PASSO 5: Criar Estrutura

```bash
mkdir -p absenteismo
cd absenteismo
pwd
```

**📤 Me envie o resultado**

---

**Aguardando você entrar na Hostinger e me passar os resultados!** ⏳



