# FIT-08 — Rollback Ready

## Status

| Item | Valor |
|------|-------|
| Rollback necessário agora? | **NÃO** |
| Rollback executado? | **NÃO** |
| Rollback pronto? | **SIM** |

## Pontos de restauração

| Tipo | Referência |
|------|------------|
| Código (padrão) | `OLD_HEAD=d0c012abaae9191531c3d2f30cb909407d31af01` |
| Código atual | `DEPLOYED_HEAD=540cda0806326aa14ced57d42fd43e8a69817d08` |
| Config | `/root/backups/absenteismo/config_pre_fit08_20260807_005949` (`.env`, `gunicorn_config.py`) |
| Banco | `/root/backups/absenteismo/absenteismo_pre_fit06_20260807_000226.db` |
| Banco SHA-256 | `13c485ace101695b792ac1dd9f634cd9291ccc381b33dbaeb79f3f316acae1ff` |

## A — Rollback de código (preferencial)

1. Confirmar necessidade (serviço/health/smoke vermelho atribuível ao tip).  
2. Em `/var/www/absenteismo`, **sem** `git clean` / `git reset --hard`:
   - `git fetch origin`
   - `git checkout d0c012abaae9191531c3d2f30cb909407d31af01`
3. Preservar `database/`, `.env`, `gunicorn_config.py`, `logs/`.  
4. Opcional: restaurar config do diretório `config_pre_fit08_20260807_005949` se a regressão for de env.  
5. `systemctl restart absenteismocontroller.service` (uma vez).  
6. Validar health + smoke resumido.  
7. **Não** restaurar banco neste caminho.

## B — Rollback de configuração

```bash
cp -a /root/backups/absenteismo/config_pre_fit08_20260807_005949/.env \
      /var/www/absenteismo/.env
# gunicorn apenas se necessário e com autorização
systemctl restart absenteismocontroller.service
```

Não imprimir `SECRET_KEY`.

## C — Rollback de banco (excepcional)

Somente com:

- evidência de corrupção / alteração indevida do SQLite vivo, **e**
- autorização humana explícita.

Procedimento resumido:

1. Parar serviço.  
2. Quarentena do banco vivo.  
3. Conferir SHA do backup `13c485ace1…`.  
4. Restaurar backup validado.  
5. Subir serviço + revalidar inventário agregado (sem PII).

**Nunca** restaurar banco automaticamente por script de deploy/smoke.

## Confirmação FIT-08

Rollback permanece **documentado e disponível**.  
**Não foi executado** porque smoke GO e produção saudável.
