# 🔧 CORRIGIR ERRO 502 (Bad Gateway)

## Problema
O Nginx está rodando, mas o Gunicorn (backend) não está respondendo.

## Solução

### PASSO 1: Verificar se o Gunicorn está rodando

No terminal da Hostinger, execute:

```bash
# Ver processos do Gunicorn
ps aux | grep gunicorn | grep -v grep

# Ver porta 8000
ss -tlnp | grep 8000
```

**Se não aparecer nada**, o Gunicorn parou.

### PASSO 2: Reiniciar o Gunicorn

```bash
cd /var/www/absenteismo
source venv/bin/activate

# Parar processos antigos (se houver)
pkill -f gunicorn

# Iniciar Gunicorn novamente
gunicorn -c gunicorn_config.py backend.main:app &

# Verificar se iniciou
ps aux | grep gunicorn | grep -v grep
```

### PASSO 3: Verificar logs

```bash
# Logs do Gunicorn
tail -50 /var/www/absenteismo/logs/app.log

# Logs do Nginx
tail -50 /var/log/nginx/absenteismo_error.log
```

### PASSO 4: Verificar configuração do Gunicorn

```bash
# Ver arquivo de configuração
cat /var/www/absenteismo/gunicorn_config.py
```

### PASSO 5: Testar conexão

```bash
# Testar se o Gunicorn responde localmente
curl http://127.0.0.1:8000/api/health
```

---

## Solução Rápida (se nada funcionar)

```bash
cd /var/www/absenteismo
source venv/bin/activate

# Matar todos os processos
pkill -9 -f gunicorn

# Aguardar 2 segundos
sleep 2

# Iniciar novamente
nohup gunicorn -c gunicorn_config.py backend.main:app > /dev/null 2>&1 &

# Verificar
ps aux | grep gunicorn | grep -v grep
curl http://127.0.0.1:8000/api/health
```

---

## Criar serviço systemd (recomendado)

Para evitar que isso aconteça novamente, crie um serviço:

```bash
nano /etc/systemd/system/absenteismo.service
```

Cole:

```ini
[Unit]
Description=AbsenteismoController API
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=/var/www/absenteismo
Environment="PATH=/var/www/absenteismo/venv/bin"
ExecStart=/var/www/absenteismo/venv/bin/gunicorn -c /var/www/absenteismo/gunicorn_config.py backend.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Depois:

```bash
systemctl daemon-reload
systemctl enable absenteismo
systemctl start absenteismo
systemctl status absenteismo
```

Agora o sistema reinicia automaticamente se cair!



