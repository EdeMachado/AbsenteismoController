# FIT-06 — Deployment Readiness (FIT06-DR1)

## Identidade

| Campo | Valor |
|-------|-------|
| DR | **FIT06-DR1** (documental; sem tag remota) |
| PR | https://github.com/EdeMachado/AbsenteismoController/pull/11 |
| Estado PR | Ready for review · aberto · base `main` |
| HEAD obrigatório (entrada FIT-06) | `fcd81f4215dfcd8c24512ea993b74c87ac624fd2` |
| App produção | `/var/www/absenteismo` |
| Banco vivo | `/var/www/absenteismo/database/absenteismo.db` |
| Serviço | `absenteismocontroller.service` · `127.0.0.1:8000` |
| Clientes | `2` CONVERPLAST · `4` RODA DE OURO |

## Produção conhecida (referência — sem alteração)

Backup histórico validado (não substitui backup atual):

- Path: `/root/backups/absenteismo/absenteismo_pre_responsividade_20260806_180357.db`
- SHA: `d45a309f79546e62fafc4a515da895a0a998c6e0ff6eb7314a9d72db19395315`

## CI (GitHub)

### Achado na entrada do FIT-06

- Workflow `Foundation CI / foundation`: **FAILURE**
- Causa: falso positivo no guard de conflict markers (`=======` batia em banners `====…` de arquivos `.txt` operacionais)
- Correção: padrão restrito a marcadores Git reais (`<<<<<<< `, `>>>>>>> `, linha exatamente `=======`)
- Arquivo: `.github/workflows/foundation-ci.yml`

### Correções aplicadas no tip FIT-06

1. Conflict-marker guard (sem falso positivo em banners `====`)
2. `ABSENTEISMO_SQLITE_PATH` descartável no workflow + `mkdir`
3. `tests/conftest.py` garante SQLite temporário antes dos imports
4. Trigger `push` em `integration/foundation-train`

**Merge humano só após CI verde no HEAD atual.**

## Declaração de banco

```
DEPLOY_DE_CODIGO_SEM_MIGRATION=true
```

- Sem SQL Epic1 no startup (flag OFF)
- Sem Performance schema
- `ensure_column(logo_url)` é no-op se já existir
- Startup não altera usuários/clientes/senhas/tenants

## Inventário esperado (após bloco SSH)

Agregados apenas — ver saída de `scripts/fit06_prod_diag_backup.sh`:

- Clientes: ids + nomes (incl. 2 e 4)
- Users: totais / ativos / inativos / admins ativos / não-admin sem tenant / contagem por `client_id`
- Table counts
- Competências por cliente (min/max mês, uploads, eventos)
- Access snapshot (admins, tenant 2/4, orphan não-admin, inativos, duplicidade username count)
- Default password hits count (sem imprimir hashes)

## Snapshot de acesso — critérios

| Check | Esperado |
|-------|----------|
| Admins ativos | ≥ 1 |
| Users tenant 2 | ≥ 1 (se operação atual exige) |
| Users tenant 4 | ≥ 1 (se operação atual exige) |
| Não-admin sem tenant | 0, ou justificado |
| Default password hits | 0 |
| Duplicate usernames | 0 |

## Variáveis necessárias

Ver `FIT06_DEPLOY_PLAN.md`. SECRET_KEY: apenas PRESENT/EMPTY — nunca valor.

## Compatibilidade

`requirements.txt`: FastAPI 0.115.0, SQLAlchemy 2.0.36, gunicorn, python-jose, python-multipart, openpyxl, pandas, fpdf2, python-pptx, bcrypt. Comparar no venv do servidor (somente leitura) antes do restart.

## Login / tokens

SECRET_KEY preservada → tokens atuais permanecem válidos até expirar (8h). Restart não revoga JWT. Frontend trata 401 com redirect login.

## Merge / Deploy / Rollback / Smoke

Documentados em:

- `FIT06_DEPLOY_PLAN.md`
- `FIT06_ROLLBACK_PLAN.md`
- `FIT06_BACKUP_PROTOCOL.md`

## Bloco SSH único

`scripts/fit06_prod_diag_backup.sh` — diagnóstico + backup + inventário sem PII. **Não executado pelo agente. Não acessa VPS automaticamente.**

## Pendências manuais no VPS (bloqueiam GO final de merge/deploy)

1. Executar o bloco SSH de backup/diagnóstico  
2. Confirmar integrity ok + SHA do backup novo  
3. Confirmar inventário/admins/tenants  
4. Confirmar env production (CORS domínio oficial, flags OFF, SECRET_KEY presente)  
5. Aguardar CI verde pós-fix do workflow  
6. Autorização humana explícita  

## Confirmações operacionais desta etapa

- Merge: **não**  
- Deploy: **não**  
- Produção/banco vivo: **não alterados** (sem acesso VPS pelo agente)  
