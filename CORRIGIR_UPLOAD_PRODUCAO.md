# 🔧 Corrigir Erro 500 Upload - Produção

## ✅ Correção Implementada

O erro 500 no upload foi corrigido no arquivo `backend/main.py` com:
- ✅ Melhor tratamento de erros com mensagens específicas
- ✅ Validação de permissões do diretório de uploads
- ✅ Correção na leitura assíncrona do arquivo
- ✅ Logs detalhados para debug

---

## 🚀 Como Aplicar no Servidor (3 Opções)

### 📋 **OPÇÃO 1: Atualizar Arquivo Específico (Mais Rápido)** ⭐ RECOMENDADO

**Execute no terminal SSH da Hostinger:**

```bash
# 1. Navegar para o diretório do sistema
cd ~/domains/absenteismocontroller.com.br/public_html/absenteismo
# OU (depende de onde está instalado):
cd ~/public_html/absenteismo

# 2. Fazer backup do arquivo atual
cp backend/main.py backend/main.py.backup

# 3. Baixar arquivo atualizado do GitHub (se usar git)
git pull
# OU transferir arquivo manualmente (veja Opção 2)

# 4. Reiniciar o serviço
# Se usar systemd:
sudo systemctl restart absenteismo
# OU (se rodar direto com gunicorn):
pkill -HUP -f gunicorn
```

---

### 📤 **OPÇÃO 2: Transferir Arquivo Manualmente**

**No seu computador (PowerShell):**

```powershell
# 1. Navegar para a pasta do projeto
cd "C:\Users\Ede Machado\AbsenteismoConverplast"

# 2. Transferir apenas o arquivo corrigido
scp -P 65002 backend/main.py usuario@ssh.hostinger.com:~/domains/absenteismocontroller.com.br/public_html/absenteismo/backend/main.py
```

**Substitua:**
- `65002` pela porta SSH da Hostinger
- `usuario` pelo seu usuário SSH
- `ssh.hostinger.com` pelo host SSH da Hostinger
- O caminho completo pode variar (verifique onde está instalado)

**OU use FileZilla:**
1. Conecte via SFTP na Hostinger
2. Navegue até `backend/`
3. Substitua o arquivo `main.py` pelo novo

**Depois, no servidor SSH:**

```bash
cd ~/domains/absenteismocontroller.com.br/public_html/absenteismo
# OU
cd ~/public_html/absenteismo

# Reiniciar serviço
sudo systemctl restart absenteismo
# OU
pkill -HUP -f gunicorn
```

---

### 🔄 **OPÇÃO 3: Atualizar Tudo via Git (Se usar Git no servidor)**

```bash
# 1. Navegar para diretório
cd ~/domains/absenteismocontroller.com.br/public_html/absenteismo
# OU
cd ~/public_html/absenteismo

# 2. Fazer backup antes
cp -r backend backend.backup.$(date +%Y%m%d_%H%M%S)

# 3. Atualizar código
git pull origin main

# 4. Verificar se há novas dependências
source venv/bin/activate
pip install -r requirements.txt

# 5. Reiniciar serviço
sudo systemctl restart absenteismo
# OU
pkill -HUP -f gunicorn
```

---

## ✅ Verificar se Correção Funcionou

**1. Verificar logs:**

```bash
# Ver logs em tempo real
tail -f logs/errors.log

# Ver logs da aplicação
tail -f logs/app.log
```

**2. Testar upload:**
- Acesse o sistema no navegador
- Tente fazer upload de uma planilha
- Se der erro 500, verifique os logs acima para ver a mensagem específica

---

## 🔍 Como Encontrar Onde Está Instalado

**Execute no SSH:**

```bash
# Procurar pelo arquivo main.py
find ~ -name "main.py" -path "*/backend/*" 2>/dev/null

# Ver processos Python rodando
ps aux | grep -E "gunicorn|python|uvicorn" | grep -v grep

# Ver diretório de trabalho do processo (mostra onde está rodando)
pwdx $(pgrep -f gunicorn)
```

---

## 🆘 Se Não Souber Como Reiniciar

**Execute estes comandos para ver como está rodando:**

```bash
# Ver processos Python
ps aux | grep python | grep -v grep

# Ver processos Gunicorn
ps aux | grep gunicorn | grep -v grep

# Ver processos na porta 8000
netstat -tlnp | grep 8000
# OU
ss -tlnp | grep 8000

# Ver serviços systemd
systemctl list-units | grep absenteismo
```

**Me envie o resultado** e eu te ajudo a reiniciar corretamente.

---

## 📝 Resumo Rápido

1. ✅ Fazer backup: `cp backend/main.py backend/main.py.backup`
2. ✅ Transferir novo `backend/main.py` (via SCP, FileZilla ou git pull)
3. ✅ Reiniciar serviço: `sudo systemctl restart absenteismo` OU `pkill -HUP -f gunicorn`
4. ✅ Testar upload no navegador
5. ✅ Verificar logs se ainda tiver erro

---

## 🎯 Após Corrigir

O erro 500 agora vai mostrar mensagens mais específicas:
- "Erro de permissão ao acessar o arquivo"
- "Erro ao salvar no banco de dados"
- "Erro de autenticação"
- etc.

**Os logs também terão mais detalhes** para identificar o problema exato.

---

**Dúvidas? Me envie:**
- O resultado dos comandos acima
- Qual opção você prefere usar
- Qualquer erro que aparecer





