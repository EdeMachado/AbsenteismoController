# RC23B — Merge Final + Deploy Plan (PREPARE ONLY)

**Status:** PR #35 MERGED · Deploy plan ready · **DEPLOY NÃO EXECUTADO**  
**Agent posture:** no VPS · no tag · no `.env` · no flag changes · no features

---

## Merge record

| Field | Value |
|-------|-------|
| PR | [#35](https://github.com/EdeMachado/AbsenteismoController/pull/35) |
| PR35_STATUS | MERGED |
| MAIN_BEFORE | `231dc635609fffbce4d2ad1512ce14efb7c202bf` |
| PR35_HEAD (tip merged) | `02e7c189f960a544177e645b21cf8f9b1cbd255e` |
| RC23 experience HEAD (ancestry) | `a1c18e448ab41a31f54875fe5062dd4b3f9c9092` |
| MERGE_COMMIT / MAIN_AFTER | `b5c4af74fe6739342b89e77b7f05402c6e890e8d` |
| Merge strategy | merge commit |
| CI (PR tip before merge) | SUCCESS (Foundation) |
| RC23A_RESULT | GO |

Note: tip moved from `a1c18e4` → `02e7c18` solely for the RC22 shell-cache CI gate (`rc23a`). Product ancestry includes `a1c18e4`; both SHAs are on `origin/main`.

---

## TARGET_HEAD (deploy)

```
TARGET_HEAD=b5c4af74fe6739342b89e77b7f05402c6e890e8d
ROLLBACK_HEAD=<VPS HEAD captured in Block1 / Block2 state>
```

Use RC17 procedure already validated (`docs/release/RC17_PRODUCTION_DEPLOY_PLAN.md` + `scripts/rc17_block*.sh`).

Override target on VPS:

```bash
export TARGET_HEAD=b5c4af74fe6739342b89e77b7f05402c6e890e8d
```

---

## Flags finais (NÃO alterar neste passo; confirmar no Block1)

```
ENVIRONMENT=production
ENABLE_EXECUTIVE_UI=true
ENABLE_EXECUTIVE_PRESENTATION=false
ENABLE_PREVIEW_SURFACES=false
ENABLE_INTELLIGENT_INGESTION=false
ENABLE_BIOMED_PERFORMANCE_ENGINE=false
ENABLE_API_DOCS=false
```

Do **not** edit `.env` during RC23B prep. Confirm values read-only in Block1; only change in a separately authorized ops step if mismatched.

---

## Sequência humana autorizada (futuro deploy)

```bash
cd /var/www/absenteismo
export TARGET_HEAD=b5c4af74fe6739342b89e77b7f05402c6e890e8d

sudo bash scripts/rc17_block1_predeploy_readonly.sh
# exige: origin/main == TARGET_HEAD, service active, health 200,
#        quick_check/integrity_check ok, SECRET_KEY present, tree clean

sudo RC17_EXECUTE=1 bash scripts/rc17_block2_backup.sh
# DB (sqlite backup) + .env + gunicorn_config.py → /root/backups/absenteismo/

sudo RC17_EXECUTE=1 TARGET_HEAD=$TARGET_HEAD bash scripts/rc17_block3_update_code.sh
# fast-forward only; abort if non-FF or origin/main != TARGET_HEAD

sudo RC17_EXECUTE=1 bash scripts/rc17_block4_dependencies.sh
sudo RC17_EXECUTE=1 bash scripts/rc17_block5_restart.sh
sudo bash scripts/rc17_block6_smoke.sh
```

Rollback (if needed):

```bash
sudo RC17_EXECUTE=1 bash scripts/rc17_block7_rollback.sh
```

---

## Smoke HTTP esperado (pós-deploy)

**200:**

- `/landing`, `/login`, `/`, `/clientes`, `/executive`, `/analytics`, `/dashboard`
- `/funcionarios`, `/upload`, `/upload_inteligente`, `/produtividade`, `/comparativos`
- `/dados_powerbi`, `/dashboard_powerbi`, `/apresentacao`, `/configuracoes`

**404 (gated OFF):**

- `/executive/presentation`
- `/preview/landing`, `/preview/ficha-digital`
- `/api/preview/ficha/templates`
- `/f/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
- `/docs`, `/redoc`, `/openapi.json`

Extend Block6 checks for routes above that are not already covered by the stock script.

---

## Smoke real obrigatório (credencial admin)

1. Landing → Entrar → **Login obrigatório** (sem auto-resume com token residual)
2. Pós-login → `/clientes` (sem empresa pré-selecionada)
3. Selecionar empresa → Home
4. Validar com dados reais: KPIs, gráficos, filtros, funcionários, uploads, comparativos, produtividade, Power BI, Executive, apresentação

Security gate: leftover `access_token` + `cliente_selecionado` must **not** skip login.

---

## Pré-requisitos / rollback readiness

| Item | Ready |
|------|-------|
| Backup DB / `.env` / gunicorn (Block2) | yes (script) |
| FF-only update (Block3) | yes |
| Dependencies + restart (Block4/5) | yes |
| Smoke + rollback scripts (Block6/7) | yes |
| VPS access from this agent | **no** — human ops only |

`ROLLBACK_READY=yes` (procedure + Block7). Execution deferred until authorized deploy step.

---

## NEXT_ACTION

**RC23C — Controlled production deploy** by human ops on VPS to `TARGET_HEAD=b5c4af74fe6739342b89e77b7f05402c6e890e8d` using RC17 blocks. Do not tag until post-deploy smoke + real-data smoke pass.
