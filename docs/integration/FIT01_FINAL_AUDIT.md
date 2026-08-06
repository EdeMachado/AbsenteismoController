# FIT-01 — Auditoria final e revisão arquitetural

## Feature flags

| Flag | Valor default | Verificação |
|------|---------------|-------------|
| `ENABLE_INTELLIGENT_INGESTION` | false | `.env.example` + `is_intelligent_ingestion_enabled()` |
| `ENABLE_BIOMED_PERFORMANCE_ENGINE` | false | `.env.example` + `is_performance_engine_enabled()` |
| Command Center / AI / Analytics novos | inexistentes | OK |

Nenhum módulo novo inicia ativo.

## Imports / acoplamento

- `performance` → `services.metric_service` / `services.data_quality_service` via adapters  
- `ingestion` → DQ via `iqb_adapter`; tenant via adapter fail-closed  
- Sem import de frontend a partir de services  

## Warnings observados nos testes

- SQLAlchemy `declarative_base` deprecated (legado `database.py`)  
- FastAPI `@app.on_event("startup")` deprecated  
- `datetime.utcnow()` em `auth.py` (legado)  

Não bloqueiam FIT-01; candidatos a hygiene futura.

## Ordem de integração validada

PR4 → PR5 → PR6 → PR8 → PR10 → docs (#9 + Executive Intelligence).  
Sem ordem superior para segurança/HTTP.
