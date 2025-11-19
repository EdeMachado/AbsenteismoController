# 🔧 CORRIGIR ARQUIVOS ESTÁTICOS - Nginx

## Problema
O sistema entra, mas não carrega CSS, JS e imagens (página incompleta).

## Solução

### PASSO 1: Verificar se os arquivos foram enviados

No terminal da Hostinger, execute:

```bash
# Verificar se a pasta frontend existe
ls -la /var/www/absenteismo/frontend/

# Verificar se os arquivos estáticos existem
ls -la /var/www/absenteismo/frontend/static/
ls -la /var/www/absenteismo/frontend/static/css/
ls -la /var/www/absenteismo/frontend/static/js/
```

### PASSO 2: Verificar configuração do Nginx

```bash
# Ver configuração atual
cat /etc/nginx/sites-available/absenteismocontroller
```

### PASSO 3: Corrigir configuração do Nginx

O Nginx precisa passar TODAS as requisições (incluindo `/static`) para o FastAPI.

Edite o arquivo:

```bash
nano /etc/nginx/sites-available/absenteismocontroller
```

A configuração deve estar assim:

```nginx
server {
    listen 80;
    server_name www.absenteismocontroller.com.br absenteismocontroller.com.br;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.absenteismocontroller.com.br absenteismocontroller.com.br;

    ssl_certificate /etc/letsencrypt/live/www.absenteismocontroller.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.absenteismocontroller.com.br/privkey.pem;

    # IMPORTANTE: Passar TUDO para o FastAPI (incluindo /static)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
    }

    # Logs
    access_log /var/log/nginx/absenteismo_access.log;
    error_log /var/log/nginx/absenteismo_error.log;
}
```

**IMPORTANTE:** Não criar `location /static` separado! O FastAPI já serve os arquivos estáticos.

### PASSO 4: Testar e recarregar

```bash
# Testar configuração
nginx -t

# Se OK, recarregar
systemctl reload nginx
```

### PASSO 5: Verificar logs

```bash
# Ver erros do Nginx
tail -f /var/log/nginx/absenteismo_error.log

# Ver requisições
tail -f /var/log/nginx/absenteismo_access.log
```

### PASSO 6: Verificar permissões (se necessário)

```bash
# Dar permissões corretas
chown -R www-data:www-data /var/www/absenteismo/frontend
chmod -R 755 /var/www/absenteismo/frontend
```

### PASSO 7: Testar no navegador

1. Abra: https://www.absenteismocontroller.com.br
2. Pressione F12 (DevTools)
3. Vá na aba "Network"
4. Recarregue a página (F5)
5. Verifique se os arquivos CSS/JS estão sendo carregados (status 200)

Se algum arquivo retornar 404, verifique o caminho no console do navegador.



