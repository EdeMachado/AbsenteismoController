# 📋 Comandos para Copiar/Colar - Hostinger

## 🔍 PASSO 1: Verificar Ambiente

```bash
python3 --version
```

```bash
pwd
whoami
```

```bash
df -h
```

---

## 📁 PASSO 2: Navegar e Criar Estrutura

```bash
cd ~/domains/absenteismocontroller.com.br/public_html
```

**OU:**

```bash
cd ~/public_html
```

```bash
mkdir -p absenteismo
cd absenteismo
pwd
```

---

## 🐍 PASSO 3: Ambiente Virtual

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

```bash
pip install --upgrade pip
```

---

## 📦 PASSO 4: Instalar Dependências

```bash
pip install -r requirements.txt
```

---

## ⚙️ PASSO 5: Criar .env

```bash
nano .env
```

**Depois de criar, gerar SECRET_KEY:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🗄️ PASSO 6: Banco de Dados

```bash
mkdir -p database
```

```bash
python3 -c "from backend.database import init_db, run_migrations; init_db(); run_migrations(); print('Banco inicializado!')"
```

---

## 🧪 PASSO 7: Testar

```bash
python3 -c "from backend.main import app; print('Sistema OK!')"
```

---

## 🚀 PASSO 8: Gunicorn

```bash
pip install gunicorn
```

```bash
nano gunicorn_config.py
```

**Conteúdo do arquivo:**
```python
bind = "127.0.0.1:8000"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
```

---

## 🔄 PASSO 9: Testar Servidor

```bash
gunicorn --config gunicorn_config.py backend.main:app
```

---

**Copie e cole cada comando conforme eu pedir!** 📋



