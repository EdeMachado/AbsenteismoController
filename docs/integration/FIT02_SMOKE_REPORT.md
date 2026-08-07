# FIT-02 — Smoke Report

## Ambiente

| Item | Valor |
|------|-------|
| Worktree / staging | `/tmp/abs-fit02-staging-*` + scripts locais |
| Porta | `18080` (uvicorn isolado; não 8000 produção) |
| DB | SQLite descartável via `ABSENTEISMO_SQLITE_PATH` |
| Flags | ambas `false` |
| Produção | não usada |

## TestClient smoke (`scripts/fit02_smoke_staging.py`)

| Passo | Resultado |
|-------|-----------|
| `/api/health` | 200 |
| login form | 200 |
| `/api/clientes` autenticado | 200 |
| `/` home | 200 |
| `/dashboard_powerbi` | 200 |
| `/api/ingestion/*` com flag off | 404 |
| upload cross-tenant | 403/404 |
| live DB used | **false** |

## Uvicorn :18080

| Passo | Resultado |
|-------|-----------|
| health JSON | 200 (`status=ok`, integrity_check true) |
| ingestion com flag off | 404 |
| processo encerrado após smoke | sim (Ctrl-C no tmux) |

## Observações

- Login atualiza `last_login` (escrita esperada apenas no DB descartável).
- Nenhum Nginx/systemd de produção utilizado.
