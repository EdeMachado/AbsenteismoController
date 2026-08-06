# FIT-06 — Protocolo de Backup Pré-Deploy (FIT06-DR1)

## Objetivo

Gerar backup SQLite **consistente** do banco vivo **sem** parar o serviço e **sem** alterar dados.

## Paths conhecidos

| Item | Path |
|------|------|
| App | `/var/www/absenteismo` |
| Banco vivo | `/var/www/absenteismo/database/absenteismo.db` |
| Destino backup | `/root/backups/absenteismo/` |
| Nome | `absenteismo_pre_fit06_<timestamp>.db` |
| Serviço | `absenteismocontroller.service` |

## Backup histórico (não substitui o atual)

- `/root/backups/absenteismo/absenteismo_pre_responsividade_20260806_180357.db`
- SHA: `d45a309f79546e62fafc4a515da895a0a998c6e0ff6eb7314a9d72db19395315`

## Script seguro (não executado pelo agente)

`scripts/fit06_prod_diag_backup.sh`

Execução manual no VPS (após autorização humana):

```bash
sudo bash /var/www/absenteismo/scripts/fit06_prod_diag_backup.sh
# ou, se o script ainda não estiver no servidor, cole o conteúdo do script via SSH
```

## O bloco realiza

1. Confirma processo/serviço e listeners `:8000`
2. Confirma path do banco
3. `PRAGMA quick_check` / `integrity_check` / `journal_mode` (live, read-only URI)
4. Backup via `sqlite3.Connection.backup` no **Python do venv** (não depende do binário `sqlite3`)
5. Salva fora do deploy (`/root/backups/absenteismo/`)
6. SHA-256 + arquivo `.sha256`
7. Cópia `.gz`
8. Valida quick/integrity do backup
9. Registra tamanho/timestamp
10. **Não** para o serviço
11. **Não** altera o banco vivo
12. Inventário agregado **sem PII**

## Critérios de falha (NO-GO)

- `quick_check` ≠ ok  
- `integrity_check` ≠ ok  
- backup inválido  
- path do banco vivo não confirmado  

## Proibições

- Não usar `cp` simples como único método (preferir API `.backup`)  
- Não sobrescrever backups existentes  
- Não imprimir username/email/hash/token/SECRET_KEY  
