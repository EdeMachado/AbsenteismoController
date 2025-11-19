# 🚀 Deploy na Hostinger - Passo a Passo

## 📋 Pré-requisitos

Antes de começar, você precisa ter:
- ✅ Conta na Hostinger
- ✅ Domínio configurado: www.absenteismocontroller.com.br
- ✅ Acesso SSH habilitado no painel da Hostinger
- ✅ Arquivos do sistema prontos (este repositório)

---

## 📦 PASSO 1: Preparar Arquivos Localmente

### 1.1 - Verificar o que temos

**Execute localmente (no seu computador):**

```bash
# Verificar estrutura do projeto
dir
```

**Me envie o resultado** para eu ver quais arquivos temos.

---

## 🔐 PASSO 2: Acessar SSH da Hostinger

### 2.1 - Obter credenciais SSH

1. Acesse o **hPanel** da Hostinger
2. Vá em **Avançado** → **SSH**
3. Anote:
   - **Host/Server:** (ex: ssh.hostinger.com)
   - **Porta:** (geralmente 65002)
   - **Usuário:** (seu usuário SSH)
   - **Senha:** (ou chave SSH)

### 2.2 - Conectar via SSH

**Use um cliente SSH:**
- **Windows:** PuTTY, Windows Terminal, ou PowerShell
- **Comando no PowerShell:**
```powershell
ssh usuario@ssh.hostinger.com -p 65002
```

**Me diga:**
- ✅ Conseguiu conectar?
- Qual é a mensagem que aparece ao conectar?

---

## 🔍 PASSO 3: Verificar Ambiente no Servidor

### 3.1 - Verificar Python

**Execute no terminal SSH:**

```bash
python3 --version
```

**Me envie o resultado.**

### 3.2 - Verificar localização

**Execute:**

```bash
pwd
whoami
```

**Me envie o resultado.**

### 3.3 - Verificar espaço em disco

```bash
df -h
```

**Me envie o resultado.**

---

## 📁 PASSO 4: Criar Estrutura de Diretórios

### 4.1 - Navegar para diretório do site

**Execute:**

```bash
cd ~/domains/absenteismocontroller.com.br/public_html
```

**OU se não existir:**

```bash
cd ~/public_html
```

**Me diga qual caminho funcionou.**

### 4.2 - Criar estrutura

**Execute:**

```bash
mkdir -p absenteismo
cd absenteismo
pwd
```

**Me envie o resultado do `pwd`.**

---

## 📤 PASSO 5: Transferir Arquivos

### Opção A: Via SCP (do seu computador)

**No seu computador (PowerShell), execute:**

```powershell
# Navegar para a pasta do projeto
cd "C:\Users\Ede Machado\AbsenteismoConverplast"

# Transferir arquivos (substitua usuario e host)
scp -P 65002 -r * usuario@ssh.hostinger.com:~/domains/absenteismocontroller.com.br/public_html/absenteismo/
```

**OU se não tiver SCP instalado, use FileZilla ou similar.**

### Opção B: Via FileZilla

1. Baixe FileZilla
2. Conecte usando credenciais FTP/SSH
3. Arraste os arquivos para o servidor

**Me diga quando os arquivos estiverem transferidos.**

---

## ✅ PASSO 6: Verificar Arquivos Transferidos

**No terminal SSH, execute:**

```bash
cd ~/domains/absenteismocontroller.com.br/public_html/absenteismo
ls -la
```

**Me envie a lista de arquivos.**

---

## 🐍 PASSO 7: Configurar Python

### 7.1 - Criar ambiente virtual

**Execute:**

```bash
python3 -m venv venv
```

**Me envie o resultado (deve criar sem erros).**

### 7.2 - Ativar ambiente virtual

```bash
source venv/bin/activate
```

**Me envie o resultado (deve aparecer `(venv)` no prompt).**

### 7.3 - Atualizar pip

```bash
pip install --upgrade pip
```

**Me envie o resultado.**

---

## 📦 PASSO 8: Instalar Dependências

### 8.1 - Instalar requirements

**Execute:**

```bash
pip install -r requirements.txt
```

**⚠️ Isso pode demorar alguns minutos.**

**Me envie o resultado final (deve mostrar "Successfully installed...").**

---

## ⚙️ PASSO 9: Configurar Variáveis de Ambiente

### 9.1 - Criar arquivo .env

**Execute:**

```bash
nano .env
```

**Cole este conteúdo (substitua SECRET_KEY pela chave gerada):**

```env
SECRET_KEY=sua-chave-secreta-aqui-gerar-uma-nova
ENVIRONMENT=production
ALLOWED_ORIGINS=https://www.absenteismocontroller.com.br,https://absenteismocontroller.com.br
```

**Para salvar no nano:**
- Pressione `Ctrl + O` (salvar)
- Pressione `Enter` (confirmar)
- Pressione `Ctrl + X` (sair)

**Me diga quando salvar.**

### 9.2 - Gerar SECRET_KEY

**Execute:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Copie a chave gerada e atualize no .env**

**Me envie: "SECRET_KEY gerada e salva"**

---

## 🗄️ PASSO 10: Inicializar Banco de Dados

### 10.1 - Criar diretório do banco

```bash
mkdir -p database
```

**Me envie: "Diretório criado"**

### 10.2 - Inicializar banco

```bash
python3 -c "from backend.database import init_db, run_migrations; init_db(); run_migrations(); print('Banco inicializado!')"
```

**Me envie o resultado.**

---

## 🧪 PASSO 11: Testar Sistema Localmente

### 11.1 - Testar importação

```bash
python3 -c "from backend.main import app; print('Sistema OK!')"
```

**Me envie o resultado.**

---

## 🚀 PASSO 12: Configurar Servidor Web

### 12.1 - Verificar se tem Gunicorn

```bash
pip install gunicorn
```

**Me envie o resultado.**

### 12.2 - Criar arquivo de configuração

```bash
nano gunicorn_config.py
```

**Cole:**

```python
bind = "127.0.0.1:8000"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
```

**Salve (Ctrl+O, Enter, Ctrl+X)**

**Me diga: "Config criado"**

---

## 🔄 PASSO 13: Testar Servidor

### 13.1 - Iniciar servidor (teste)

```bash
gunicorn --config gunicorn_config.py backend.main:app
```

**Deixe rodando e me diga se apareceu alguma mensagem de erro.**

**Se funcionar, pressione Ctrl+C para parar.**

---

## 📝 PASSO 14: Configurar Serviço (Systemd ou Supervisor)

**Me diga:**
- A Hostinger permite criar serviços systemd?
- Ou prefere usar supervisor/PM2?

**Vou te passar o próximo passo baseado na resposta.**

---

## 🌐 PASSO 15: Configurar Domínio

### 15.1 - Verificar configuração do domínio

**No hPanel:**
1. Vá em **Domínios**
2. Verifique se `www.absenteismocontroller.com.br` está apontando para o diretório correto

**Me diga o caminho configurado.**

---

## 🔒 PASSO 16: Configurar SSL

### 16.1 - Ativar SSL no hPanel

1. Vá em **SSL** no hPanel
2. Ative SSL gratuito (Let's Encrypt)
3. Aguarde alguns minutos

**Me diga quando estiver ativo.**

---

## ✅ PASSO 17: Testes Finais

### 17.1 - Testar acesso

**Acesse no navegador:**
- https://www.absenteismocontroller.com.br

**Me diga:**
- ✅ Carregou a página?
- ❌ Qual erro apareceu?

---

## 📊 Próximos Passos

Depois que tudo estiver funcionando:
1. Upload de planilhas
2. Configurar backup automático
3. Monitorar logs

---

## 🆘 Troubleshooting

Se algo der errado em qualquer passo:
1. **Me envie a mensagem de erro completa**
2. **Me diga em qual passo parou**
3. **Vou te ajudar a resolver**

---

**Vamos começar pelo PASSO 1!** 🚀

Me envie o resultado do `dir` do seu computador.



