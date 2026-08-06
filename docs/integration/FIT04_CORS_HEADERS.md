# FIT-04 — CORS, Headers e Cache

## CORS (`backend/cors_config.py`)

| Ambiente | Política |
|----------|----------|
| production | Sem `*`. Origens só via `CORS_ALLOWED_ORIGINS` (lista). Default: `[]` (same-origin). |
| staging/dev/test | Configurável; sem wildcard silencioso. |

`allow_credentials` só quando há origens explícitas (nunca com `*`).

## Headers (middleware existente + FIT-04)

- `Content-Security-Policy`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy`
- `Strict-Transport-Security` apenas em HTTPS

## Cache

- `/static/*`: cache público longo
- `/api/*`: `no-store` / `no-cache` / `private`
- login e `/api/export/*`: `Expires: 0` + pragma no-cache

## Docs OpenAPI

`api_docs_enabled()` — off em production por default (`ENABLE_API_DOCS` override).

## Testes

`tests/test_fit04_cors_headers.py`
