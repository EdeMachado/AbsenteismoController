# FIT-02 — Staging Validation Gate

**Branch:** `integration/foundation-train`  
**HEAD inicial obrigatório:**   
**HEAD final FIT-02:** `ee8149a9dc0e3dfab419627de2361645bd2a18cd`  
**PR:** [#11](https://github.com/EdeMachado/AbsenteismoController/pull/11) (draft)  
**Base:** `origin/main`

---

## 1. Baseline

| Item | Status |
|------|--------|
| Branch correta | OK |
| HEAD inicial | `ee8149a` |
| PR #11 draft | OK |
| Worktree isolado | `/tmp/abs-fit02-staging-*` |
| Untracked local (auditorias/backups) | **não** incluídos em commits |

## 2. Ambiente staging

- Checkout detached / worktree no HEAD obrigatório  
- Python do sistema + `PYTHONPATH` (venv indisponível sem `python3-venv`)  
- DB SQLite descartável (`ABSENTEISMO_SQLITE_PATH`)  
- Porta `18080` para uvicorn  
- Flags inicialmente OFF  
- Sem `/var/www/absenteismo/database/absenteismo.db`

## 3. Feature flags

| Flag | Default | Validação OFF | Validação ON (só descartável) |
|------|---------|---------------|-------------------------------|
| `ENABLE_INTELLIGENT_INGESTION` | false | rotas ausentes / 404 | testes ingestion + schema SQL explícito |
| `ENABLE_BIOMED_PERFORMANCE_ENGINE` | false | sem HTTP novo | shadow/CLI interno |

## 4. Banco sintético

Dois tenants sintéticos (FIT-02 / smoke): Empresa A/B ou IDs 101/102, 201, 301.  
Usuários admin/tenant com e-mails `@fit02.test`. Sem PII real.

## 5–9. Módulos validados

| Área | Resultado |
|------|-----------|
| Regressão legada (health/login/clientes/páginas) | OK via smoke |
| Segurança/tenant (S01-A + FIT-02 matrix) | Parcial — ver blockers |
| Ingestão | OK em testes; conexão per-request corrigida |
| Métricas canônicas | OK |
| IQB | OK |
| Performance Engine shadow | OK (`ROI_NAO_CALCULAVEL` sem custos) |

## 10. Ciclo de conexão (correção)

**Problema:** `get_ingestion_repository()` abria `sqlite3.connect` por chamada HTTP sem `close()` → vazamento / risco multi-worker.

**Correção:**

- `ingestion_repository_session()` context manager  
- Handlers em `api.py` usam `with ingestion_repository_session()`  
- Override injetado não é fechado pelo handler  
- Path-backed sempre fecha no `finally`  
- Testes em `tests/ingestion/test_connection_lifecycle.py`

## 11. Testes e cobertura

| Métrica | Valor |
|---------|-------|
| Total | **408 passed** |
| Duração | ~40 s |
| Falhas | 0 (suíte final) |
| Warnings | deprecations legado (`on_event`, `utcnow`, `declarative_base`) |
| Cobertura pacotes fundação | **≈ 89%** (FIT-01: 89%) |

## 12. Startup

Confirmado por `test_s01a_startup_*` + smoke: sem reset de senha/tenant/admin padrão; `init_db`/`run_migrations` leves apenas no DB apontado; ingestion schema **não** auto-aplicado.

## 13–14. Smoke e performance mínima

Ver `FIT02_SMOKE_REPORT.md`. Sem regressões evidentes de lock; full-scan legado permanece dívida conhecida (fora do escopo de otimização FIT-02).

## 15. Correções aplicadas nesta etapa

1. Fechamento de conexões ingestion per request  
2. Bridge PR #4 (`pr4_bridge.py`) + wiring em `main.py`  
3. Override `ABSENTEISMO_SQLITE_PATH` com recusa do path vivo  
4. Suíte FIT-02 + testes de conexão/bridge  
5. Documentação FIT-02  

## 16. Decisão

Ver `FIT02_GO_NO_GO.md` → **NO-GO** para merge/produção devido a endpoints críticos legados ainda sem auth (matriz de segurança).  
Fundação shadow/flagged: validada para continuar desenvolvimento do Intelligence **sem** merge.
