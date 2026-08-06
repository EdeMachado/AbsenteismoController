# FIT-04 — CI Report

## Workflow

`.github/workflows/foundation-ci.yml`

Triggers: `pull_request` → `main`, `integration/foundation-train`

### Steps

1. Setup Python 3.12  
2. `requirements.txt` + `requirements-dev.txt`  
3. `py_compile` / import check  
4. Conflict markers guard  
5. Forbid `.db` / `.env` / backup artifacts in added files  
6. Security/inventory subset  
7. Full `pytest tests/`  
8. Coverage gate foundation packages (`--cov-fail-under=87`)

### Não executa

- Deploy  
- Secrets de produção  
- Browser Playwright (gate local — ver `FIT04_BROWSER_VALIDATION.md`)

## Dependências

- Runtime: `requirements.txt` (+ `gunicorn` para produção)  
- Dev/test: `requirements-dev.txt` (pytest, pytest-cov, playwright opcional)

## Cobertura medida (FIT-04)

Suíte completa sobre pacotes fundação (auth, authz, tenant, cors, registry, metrics, data_quality, ingestion, performance): **~87%** (expansão vs FIT-02 ~89% em superfície menor).
