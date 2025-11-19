# Guia de Deploy para Produção
## www.absenteismocontroller.com.br

Este guia detalha como fazer o deploy do sistema para produção no domínio www.absenteismocontroller.com.br

## 📋 Pré-requisitos

### 1. Servidor
- Servidor Linux (Ubuntu 20.04+ recomendado) ou Windows Server
- Python 3.10+ instalado
- Acesso root/sudo

### 2. Domínio
- Domínio configurado: www.absenteismocontroller.com.br
- DNS apontando para o servidor
- Certificado SSL (Let's Encrypt recomendado)

### 3. Banco de Dados
- SQLite (já incluído) ou PostgreSQL/MySQL para maior escala

## 🚀 Opção 1: Deploy com Nginx + Gunicorn (Recomendado)

### Passo 1: Preparar Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx
```

### Passo 2: Clonar/Transferir Código

```bash
# Criar diretório
sudo mkdir -p /var/www/absenteismocontroller
sudo chown $USER:$USER /var/www/absenteismocontroller

# Transferir arquivos (use scp, rsync ou git)
# Exemplo com git:
cd /var/www/absenteismocontroller
git clone <seu-repositorio> .
```

### Passo 3: Configurar Ambiente Virtual

```bash
cd /var/www/absenteismocontroller

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Instalar Gunicorn
pip install gunicorn
```

### Passo 4: Configurar Variáveis de Ambiente

```bash
# Criar arquivo .env
nano .env
```

Conteúdo do `.env`:
```env
SECRET_KEY=sua-chave-secreta-muito-longa-aqui
ENVIRONMENT=production
DATABASE_URL=sqlite:///./database/absenteismo.db
```

**IMPORTANTE:** Gere uma SECRET_KEY segura:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Passo 5: Configurar Gunicorn

Criar arquivo `gunicorn_config.py`:
```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
```

### Passo 6: Criar Systemd Service

Criar arquivo `/etc/systemd/system/absenteismocontroller.service`:
```ini
[Unit]
Description=AbsenteismoController Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/absenteismocontroller
Environment="PATH=/var/www/absenteismocontroller/venv/bin"
ExecStart=/var/www/absenteismocontroller/venv/bin/gunicorn \
    --config gunicorn_config.py \
    backend.main:app

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Ativar serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable absenteismocontroller
sudo systemctl start absenteismocontroller
sudo systemctl status absenteismocontroller
```

### Passo 7: Configurar Nginx

Criar arquivo `/etc/nginx/sites-available/absenteismocontroller`:
```nginx
server {
    listen 80;
    server_name www.absenteismocontroller.com.br absenteismocontroller.com.br;

    # Redirecionar HTTP para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.absenteismocontroller.com.br absenteismocontroller.com.br;

    # Certificados SSL (serão configurados pelo certbot)
    ssl_certificate /etc/letsencrypt/live/www.absenteismocontroller.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.absenteismocontroller.com.br/privkey.pem;

    # Configurações SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Tamanho máximo de upload (para planilhas grandes)
    client_max_body_size 50M;

    # Logs
    access_log /var/log/nginx/absenteismocontroller_access.log;
    error_log /var/log/nginx/absenteismocontroller_error.log;

    # Servir arquivos estáticos
    location /static/ {
        alias /var/www/absenteismocontroller/frontend/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy para aplicação
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        
        # Timeouts para uploads grandes
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

Ativar site:
```bash
sudo ln -s /etc/nginx/sites-available/absenteismocontroller /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Passo 8: Configurar SSL com Let's Encrypt

```bash
sudo certbot --nginx -d www.absenteismocontroller.com.br -d absenteismocontroller.com.br
```

Certbot irá:
- Configurar certificados SSL
- Atualizar configuração do Nginx
- Configurar renovação automática

### Passo 9: Configurar Permissões

```bash
# Criar diretórios necessários
sudo mkdir -p /var/www/absenteismocontroller/{uploads,exports,logs,database}
sudo chown -R www-data:www-data /var/www/absenteismocontroller
sudo chmod -R 755 /var/www/absenteismocontroller
```

## 🪟 Opção 2: Deploy no Windows Server

### Passo 1: Instalar Python e Dependências

```powershell
# Instalar Python 3.10+
# Baixar de python.org

# Instalar dependências
pip install -r requirements.txt
pip install waitress
```

### Passo 2: Criar Serviço Windows

Criar arquivo `start_production.py`:
```python
from waitress import serve
from backend.main import app
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    serve(app, host=host, port=port, threads=4)
```

### Passo 3: Configurar IIS como Reverse Proxy

1. Instalar URL Rewrite e Application Request Routing no IIS
2. Configurar regras de proxy para `http://localhost:8000`
3. Configurar SSL no IIS

## 📦 Opção 3: Deploy com Docker (Recomendado para Escalabilidade)

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Criar diretórios
RUN mkdir -p uploads exports logs database

# Expor porta
EXPOSE 8000

# Comando de inicialização
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "backend.main:app"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    volumes:
      - ./database:/app/database
      - ./uploads:/app/uploads
      - ./exports:/app/exports
      - ./logs:/app/logs
    restart: always
```

## 🔒 Configurações de Segurança para Produção

### 1. Atualizar CORS no main.py

```python
# Em backend/main.py, linha ~90
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.absenteismocontroller.com.br",
        "https://absenteismocontroller.com.br"
    ],  # Especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

### 2. Configurar Rate Limiting Mais Restritivo

```python
# Em backend/main.py
RATE_LIMIT_MAX_REQUESTS = 60  # Reduzir para produção
```

### 3. Desabilitar Debug

Certifique-se de que `ENVIRONMENT=production` está no `.env`

## 📊 Monitoramento

### Logs

```bash
# Ver logs da aplicação
sudo journalctl -u absenteismocontroller -f

# Ver logs do Nginx
sudo tail -f /var/log/nginx/absenteismocontroller_access.log
sudo tail -f /var/log/nginx/absenteismocontroller_error.log

# Ver logs da aplicação
tail -f /var/www/absenteismocontroller/logs/app.log
tail -f /var/www/absenteismocontroller/logs/security.log
```

### Backup Automático

Configurar cron job para backup diário:
```bash
# Adicionar ao crontab
0 2 * * * /usr/bin/python3 /var/www/absenteismocontroller/backup_banco.py
```

## 🔄 Atualizações

### Processo de Atualização

```bash
# 1. Fazer backup
python backup_banco.py

# 2. Parar serviço
sudo systemctl stop absenteismocontroller

# 3. Atualizar código
git pull  # ou transferir novos arquivos

# 4. Atualizar dependências
source venv/bin/activate
pip install -r requirements.txt

# 5. Executar migrações (se houver)
python -c "from backend.database import run_migrations; run_migrations()"

# 6. Reiniciar serviço
sudo systemctl start absenteismocontroller
sudo systemctl status absenteismocontroller
```

## ✅ Checklist de Deploy

- [ ] Servidor configurado
- [ ] Python e dependências instaladas
- [ ] Arquivo `.env` criado com SECRET_KEY
- [ ] Banco de dados inicializado
- [ ] Serviço systemd configurado e rodando
- [ ] Nginx configurado e testado
- [ ] SSL configurado (Let's Encrypt)
- [ ] CORS atualizado para domínio de produção
- [ ] Rate limiting configurado
- [ ] Logs configurados
- [ ] Backup automático configurado
- [ ] Testes realizados
- [ ] Monitoramento configurado

## 🆘 Troubleshooting

### Serviço não inicia
```bash
sudo systemctl status absenteismocontroller
sudo journalctl -u absenteismocontroller -n 50
```

### Erro 502 Bad Gateway
- Verificar se Gunicorn está rodando: `sudo systemctl status absenteismocontroller`
- Verificar logs do Nginx
- Verificar se porta 8000 está acessível

### Erro de permissões
```bash
sudo chown -R www-data:www-data /var/www/absenteismocontroller
sudo chmod -R 755 /var/www/absenteismocontroller
```

## 📞 Suporte

Para problemas, verificar:
1. Logs da aplicação (`logs/`)
2. Logs do Nginx
3. Status do serviço systemd
4. Certificados SSL

---

**Última atualização:** 2025-01-16



