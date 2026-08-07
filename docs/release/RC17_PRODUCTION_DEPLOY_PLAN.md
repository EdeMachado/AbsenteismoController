# RC-1.7 — Production Deploy Plan (PREPARE ONLY)

**Status:** Plan + scripts ready · **DEPLOY NÃO EXECUTADO**  
**Agent posture:** no VPS mutate · no restart · no migration · no flag enable · no `.env` edit

---

## Baseline (reconfirmado)

| Item | SHA |
|------|-----|
| PRODUCTION_EXPECTED_HEAD (pré-deploy) | `540cda0806326aa14ced57d42fd43e8a69817d08` |
| MAIN_RELEASE_MERGE (PR #25) | `9ed88591f08a5261abb09d7d9e03493a52dff2c3` |
| TARGET_HEAD / MAIN_CURRENT | `fefa1996d37004c88dfb2087166544ea05be9e8f` |

Delta `9ed8859..fefa199`: **somente documentação RC-1.6** (`docs/release/RC16_CONTROLLED_MERGE_REPORT.md`).

Tree do código de produto no TARGET = tip do merge #25 + docs.

---

## Objetivo do deploy

Atualizar produção para `fefa199…` com **todas** as experiências novas **OFF**.

Comportamento esperado pós-deploy (flags OFF):

- Superfície legada íntegra (login, clientes, upload, dashboard, etc.)
- Preview/homologação **bloqueados** (`ENABLE_PREVIEW_SURFACES` fail-closed)
- Ficha Digital **PREVIEW_ONLY** (não liberar)
- Sem migration obrigatória
- `SECRET_KEY` e CORS oficiais preservados

---

## Layout de produção (conhecido)

| Item | Path / valor |
|------|----------------|
| App | `/var/www/absenteismo` |
| DB | `/var/www/absenteismo/database/absenteismo.db` |
| Serviço | `absenteismocontroller.service` |
| Listen | `127.0.0.1:8000` |
| Backups | `/root/backups/absenteismo/` |
| Venv | `/var/www/absenteismo/venv` |

---

## Scripts (ordem obrigatória)

| Block | Script | Mutação | Gate |
|-------|--------|---------|------|
| 1 | `scripts/rc17_block1_predeploy_readonly.sh` | Nenhuma (read-only) | GO conditions |
| 2 | `scripts/rc17_block2_backup.sh` | Cria backup fora do tree | `RC17_EXECUTE=1` |
| 3 | `scripts/rc17_block3_update_code.sh` | Fast-forward code only | `RC17_EXECUTE=1` |
| 4 | `scripts/rc17_block4_dependencies.sh` | pip + compile/import | `RC17_EXECUTE=1` |
| 5 | `scripts/rc17_block5_restart.sh` | restart serviço | `RC17_EXECUTE=1` |
| 6 | `scripts/rc17_block6_smoke.sh` | smoke HTTP + DB RO | |
| 7 | `scripts/rc17_block7_rollback.sh` | checkout OLD_HEAD | `RC17_EXECUTE=1` |

### Sequência humana autorizada (futuro)

```bash
cd /var/www/absenteismo
sudo bash scripts/rc17_block1_predeploy_readonly.sh          # exige GO
sudo RC17_EXECUTE=1 bash scripts/rc17_block2_backup.sh       # exige GO
sudo RC17_EXECUTE=1 bash scripts/rc17_block3_update_code.sh
sudo RC17_EXECUTE=1 bash scripts/rc17_block4_dependencies.sh
sudo RC17_EXECUTE=1 bash scripts/rc17_block5_restart.sh
sudo bash scripts/rc17_block6_smoke.sh                       # exige GO
```

**Não executar nesta etapa RC-1.7 de preparação.**

---

## Block1 — GO conditions

- `origin/main == fefa1996d37004c88dfb2087166544ea05be9e8f`
- serviço `active`
- health `200`
- DB `quick_check=ok` + `integrity_check=ok`
- `SECRET_KEY` presente (valor **nunca** impresso)
- tracked tree clean
- backup possível (paths/venv)
- `ROLLBACK_HEAD` conhecido (`git rev-parse HEAD`)
- `MIGRATION_REQUIRED=no`

---

## Block2 — Backup

Backup obrigatório **antes** de qualquer alteração:

- DB via `sqlite3.Connection.backup` (venv Python)
- `.env` (cópia; conteúdo não impresso)
- `gunicorn_config.py`

Registrar: timestamp, SHA-256, tamanho, permissões, caminho.  
Validar backup com `PRAGMA quick_check` / `integrity_check`.  
**Não** compactar/remover backups anteriores como passo destrutivo (cópias novas apenas).

---

## Flags / config (não ativar)

Garantir / documentar:

```
ENVIRONMENT=production
ENABLE_EXECUTIVE_UI=false
ENABLE_EXECUTIVE_PRESENTATION=false
ENABLE_INTELLIGENT_INGESTION=false
ENABLE_BIOMED_PERFORMANCE_ENGINE=false
ENABLE_API_DOCS=false
ENABLE_PREVIEW_SURFACES=false
```

Se ausentes: defaults fail-closed do app (production-like OFF).  
**Não** alterar `SECRET_KEY`. Preservar `CORS_ALLOWED_ORIGINS` oficial (sem `*`).

---

## Ficha Digital

`DIGITAL_FORM_STATUS=PREVIEW_ONLY`

Em produção (gate):

- `/preview/*` (exceto legado `/preview`) → 404  
- `/staging/*` → 404  
- `/api/preview/ficha/*` → 404  
- `/f/*` → 404  

Sem persistência · sem migration · sem liberação neste deploy.

---

## Block3 — Update code

- `git fetch origin`
- confirmar `origin/main` == TARGET
- salvar `OLD_HEAD`
- **somente** `git merge --ff-only origin/main`
- **proibido:** `reset --hard`, `clean`
- preservar `database/`, `.env`, `gunicorn_config.py`, `logs/`, `nohup.out`
- abort se HEAD ≠ `fefa199…`

---

## Block4 — Dependencies

- `venv/bin/pip install -r requirements.txt`
- `python -m compileall backend`
- `import backend.main`
- `inventory_unclassified(app) == []`

---

## Block5 — Restart

- `systemctl restart absenteismocontroller.service` **somente**
- validar active · journal · `:8000` · health
- falha → **rollback de código** imediato (Block7), **sem** restore automático de DB

---

## Block6 — Smoke

Health, home, login, clientes, funcionarios, upload, produtividade, powerbi pages,  
APIs protegidas anon→401, docs/preview/staging/ficha/`/f/*`→404,  
headers, CORS aleatório ausente, DB integrity, clientes **2** e **4**, contagens,  
`LEGACY_WITH_FLAGS_OFF=PASS`.

---

## Block7 — Rollback

- checkout `OLD_HEAD` (sem clean)
- config restore só com `RC17_RESTORE_CONFIG=1` + `RC17_BACKUP_DIR`
- DB restore **somente** decisão humana explícita (fora do script automático)
- restart + health

---

## Migration

```
MIGRATION_REQUIRED=no
DEPLOY_DE_CODIGO_SEM_MIGRATION=true
```

`run_migrations()` apenas `ensure_column(clients.logo_url)` — no-op se já existe.

---

## Segurança

Não imprimir: `SECRET_KEY`, password hashes, tokens, dados clínicos, CPF, matrícula.

---

## Decisão desta etapa

| Item | Valor |
|------|-------|
| RC17_PLAN_RESULT | **GO** (plano/scripts prontos) |
| Deploy executado | **no** |
| VPS mutado | **no** |
| BACKUP_PLAN_READY | yes |
| ROLLBACK_PLAN_READY | yes |
| FLAGS_WILL_REMAIN_OFF | yes |
| PREVIEW_SURFACES_BLOCKED | yes |

### NEXT_ACTION

Autorização humana explícita para executar Blocks 1→6 no VPS (RC-1.8 deploy execution).  
Até lá: **PARAR · NÃO EXECUTAR DEPLOY.**
