# FIT-04 — Resource Ownership

## Política

Tenant não depende só de `client_id` na query. O backend resolve o tenant real do recurso e aplica `validar_acesso_client_id` / `resolve_authorized_client`.

| Recurso | Acesso cruzado esperado | Evidência |
|---------|-------------------------|-----------|
| `cliente_id` | 403 | `test_fit04_resource_ownership` |
| `upload_id` (preview/delete) | 403 / 404 | idem |
| `produtividade_id` | 403 | idem |
| `atestado_id` (sem query) | 403 | idem |
| perfil funcionário | 403 | idem |
| orphan / inactive | 403 / 401 | idem |

## Correções FIT-04

- `GET /api/export/excel` e `GET /api/export/pptx`: passaram a usar `resolve_authorized_client` (antes só `validar_client_id` — vazamento cross-tenant autenticado).
- `GET/POST /api/filtros-salvos`: tenant assert adicionado.

## Mutações

Cobertura em `tests/test_fit04_mutations.py`: create cliente (admin), produtividade própria vs cruzada, clone admin-only, delete cliente admin-only.
