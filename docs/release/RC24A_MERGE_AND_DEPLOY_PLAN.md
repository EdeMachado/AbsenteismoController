# RC24A — Final Merge + Production Deploy Plan (PREPARE ONLY)

**Status:** PR #37 MERGED · Deploy plan ready · **DEPLOY NÃO EXECUTADO**  
**Agent posture:** no VPS · no tag · no `.env` · no flag changes · no features · no DB/API

**This is the last deploy of BioMed Platform v2.1.**

---

## Merge record

| Field | Value |
|-------|-------|
| PR | [#37](https://github.com/EdeMachado/AbsenteismoController/pull/37) |
| PR37_STATUS | MERGED |
| MAIN_BEFORE | `b5c4af74fe6739342b89e77b7f05402c6e890e8d` |
| PR37_HEAD | `f0f5dae4da02e2fcd83ed3a1a516692cd451eca9` |
| MERGE_COMMIT / MAIN_AFTER | `ad8b7578a220942e29e9591281b7d665c9116769` |
| Merge strategy | merge commit |
| CI (PR tip before merge) | SUCCESS (Foundation) |
| RC24_RESULT | GO |

`origin/main` contains `f0f5dae…` (RC24 polish tip) via merge commit `ad8b757…`.

---

## TARGET_HEAD (deploy)

```
TARGET_HEAD=ad8b7578a220942e29e9591281b7d665c9116769
ROLLBACK_HEAD=<VPS HEAD captured in Block1 / Block2 state>
```

What lands in production vs prior main (`b5c4af7` / RC23):

- `frontend/static/css/biomed-polish.css` (new)
- Shell `CACHE=rc24` + polish CSS wiring
- Apresentação empty-state / brand fallback polish
- HTML cache-bust `rc24`
- Release tests + docs

**No migrations. No DB schema changes. No API contract changes. No flag changes.**

---

## Flags finais (confirmar read-only; NÃO alterar neste passo)

```
ENVIRONMENT=production
ENABLE_EXECUTIVE_UI=true
ENABLE_EXECUTIVE_PRESENTATION=false
ENABLE_PREVIEW_SURFACES=false
ENABLE_INTELLIGENT_INGESTION=false
ENABLE_BIOMED_PERFORMANCE_ENGINE=false
ENABLE_API_DOCS=false
```

---

## Sequência humana autorizada (RC17)

```bash
cd /var/www/absenteismo
export TARGET_HEAD=ad8b7578a220942e29e9591281b7d665c9116769

sudo bash scripts/rc17_block1_predeploy_readonly.sh
# exige: origin/main == TARGET_HEAD, service active, health 200,
#        quick_check/integrity_check ok, SECRET_KEY present, tree clean
#        MIGRATION_REQUIRED=no

sudo RC17_EXECUTE=1 bash scripts/rc17_block2_backup.sh
# DB (sqlite backup) + .env + gunicorn_config.py → /root/backups/absenteismo/

sudo RC17_EXECUTE=1 TARGET_HEAD=$TARGET_HEAD bash scripts/rc17_block3_update_code.sh
# fast-forward only; abort if non-FF or origin/main != TARGET_HEAD

sudo RC17_EXECUTE=1 bash scripts/rc17_block4_dependencies.sh
sudo RC17_EXECUTE=1 bash scripts/rc17_block5_restart.sh
sudo bash scripts/rc17_block6_smoke.sh
```

Rollback:

```bash
sudo RC17_EXECUTE=1 bash scripts/rc17_block7_rollback.sh
```

---

## Smoke HTTP esperado (pós-deploy)

**200:** `/landing` `/login` `/` `/clientes` `/executive` `/analytics` `/dashboard` `/funcionarios` `/upload` `/upload_inteligente` `/produtividade` `/comparativos` `/dados_powerbi` `/dashboard_powerbi` `/apresentacao` `/configuracoes`

**404:** `/executive/presentation` `/preview/landing` `/preview/ficha-digital` `/api/preview/ficha/templates` `/f/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` `/docs` `/redoc` `/openapi.json`

Confirm static polish asset: `/static/css/biomed-polish.css` → 200 and shell `CACHE=rc24`.

---

## Smoke real obrigatório

Landing → Entrar → Login → `/clientes` → selecionar empresa → Home  
Validar: KPIs, gráficos, filtros, funcionários, uploads, comparativos, produtividade, Power BI, Executive, apresentação (empty `— / —` if no data; immersive deck).

Responsive spot-check: 1440 / 1366 / 768 / 390 — no overflow-x, no button overlap.

---

## Readiness

| Item | Ready |
|------|-------|
| DEPLOY_PLAN_READY | yes |
| ROLLBACK_READY | yes (Block7 + backup Block2) |
| Migrations | none |
| VPS access from this agent | **no** — human ops only |

---

## NEXT_ACTION

**Human/VPS controlled deploy** of `TARGET_HEAD=ad8b7578a220942e29e9591281b7d665c9116769` using RC17 blocks.  
Do **not** create a git tag in this step. Tag only after post-deploy smoke + real-data smoke pass (separate ops decision).
