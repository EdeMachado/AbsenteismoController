# 🔍 DIAGNÓSTICO GUNICORN

Execute estes comandos no terminal da Hostinger:

```bash
cd /var/www/absenteismo
source venv/bin/activate

# Ver logs recentes
tail -50 /var/www/absenteismo/logs/app.log
tail -50 /var/www/absenteismo/logs/errors.log

# Verificar configuração do Gunicorn
cat gunicorn_config.py

# Tentar iniciar de forma verbosa (para ver erros)
gunicorn -c gunicorn_config.py backend.main:app
```

Isso vai mostrar os erros em tempo real. Pressione Ctrl+C para parar.



