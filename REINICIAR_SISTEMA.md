# 🔄 REINICIAR SISTEMA - Hostinger

## Verificar como está rodando

Execute no terminal da Hostinger:

```bash
# Ver processos Python/Gunicorn rodando
ps aux | grep -E "gunicorn|python|uvicorn" | grep -v grep

# Ver se há processo na porta 8000
netstat -tlnp | grep 8000
# OU
ss -tlnp | grep 8000
```

## Opções para reiniciar

### Opção 1: Se estiver rodando com Gunicorn diretamente

```bash
# Encontrar o PID
ps aux | grep gunicorn | grep -v grep

# Matar o processo (substitua PID pelo número encontrado)
kill -HUP PID

# OU reiniciar manualmente
pkill -f gunicorn
cd /var/www/absenteismo
source venv/bin/activate
gunicorn -c gunicorn_config.py backend.main:app &
```

### Opção 2: Criar serviço systemd (recomendado)

Criar arquivo de serviço:

```bash
nano /etc/systemd/system/absenteismo.service
```

Cole este conteúdo:

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
# Recarregar systemd
systemctl daemon-reload

# Habilitar serviço
systemctl enable absenteismo

# Iniciar serviço
systemctl start absenteismo

# Verificar status
systemctl status absenteismo
```

### Opção 3: Reiniciar Nginx (pode ajudar)

```bash
systemctl reload nginx
```



