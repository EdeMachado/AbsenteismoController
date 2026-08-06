# FIT-03 — Validação (staging local descartável)

**Branch:** `integration/foundation-train`  
**Baseline:** `79fac6a946c3276a13a60be0724d5d6b8c49ec3c`

## Escopo executado

1. Inventário FastAPI real (`app.routes`) — 96 handlers (76 API + 20 HTML).
2. Dependências centrais em `backend/authz.py` (reuso PR #4 / `resolve_authorized_client`).
3. Middleware Bearer em `/api/*` (allowlist: login, health).
4. Proteção Depends em rotas que estavam abertas no FIT-02.
5. Semântica NULL/`is_admin` alinhada.
6. Docs OpenAPI condicionais; health sanitizado; integrity admin-only.
7. Matriz 100% em `FIT03_ENDPOINT_SECURITY_MATRIX.md`.
8. Testes: `tests/test_fit03_api_auth_smoke.py` + extensão S01-A.

## Não executado (proibido)

- Acesso VPS / produção / banco vivo  
- Migration / seed / alteração de usuários ou clientes reais  
- Merge / deploy / ligar flags em produção  
- Novas funcionalidades / UX / IA  

## Evidências esperadas de teste

```bash
pytest tests/test_fit03_api_auth_smoke.py tests/test_s01a_tenant_guard.py -q
pytest tests/ -q
```

## Frontend

Páginas principais carregam `auth.js` (Bearer interceptor). Shell HTML permanece público; APIs de negócio exigem token. Sem alteração visual.
