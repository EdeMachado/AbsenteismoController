# FIT-06 — Plano de Rollback

## Princípio

Preferir **rollback de código** preservando o banco. Restaurar backup do banco **somente** com evidência de alteração/corrupção e autorização explícita.

## A — Rollback de código (padrão)

1. Anotar SHA quebrado e SHA anterior de produção  
2. Em `/var/www/absenteismo`:
   - `git fetch origin`
   - `git checkout <SHA_ANTERIOR>` **sem** `git clean`
3. Preservar `database/`, `gunicorn_config.py`, `logs/`  
4. Reinstalar requirements do SHA anterior **somente se** o import falhar  
5. `systemctl restart absenteismocontroller.service` (uma vez)  
6. Validar: status · `/api/health` · login · dashboard · clientes 2 e 4  
7. Confirmar tamanho/integrity do banco vivo (somente leitura)

## B — Rollback de banco (excepcional)

**Não é padrão** para este deploy (`DEPLOY_DE_CODIGO_SEM_MIGRATION=true`).

Só considerar se:

- `integrity_check` falhar após o deploy, **ou**
- houver evidência de escrita/corrupção atribuível ao deploy

Procedimento (autorização humana obrigatória):

1. Parar serviço  
2. Copiar banco suspeito para quarentena (`/root/backups/absenteismo/quarantine_<ts>.db`)  
3. Restaurar `absenteismo_pre_fit06_<ts>.db` validado (SHA conferido) para o path vivo  
4. Subir serviço  
5. Revalidar inventário agregado (sem PII)  
6. Registrar incidente  

**Nunca** substituir o banco automaticamente por script de deploy.

## O que não fazer

- Não apagar backups  
- Não misturar restore de banco com experimento de flag  
- Não reaplicar Epic1 SQL  
- Não resetar senhas/tenants como “atalho” de rollback  
