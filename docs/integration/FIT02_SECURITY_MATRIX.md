# FIT-02 — Matriz de Segurança / Tenant

**Branch:** `integration/foundation-train`  
**Escopo:** auditoria de exposição HTTP + isolamento tenant na fundação integrada.

## Endpoints protegidos (amostra S01-A / críticos cobertos por testes)

| Endpoint | Auth | Tenant | Evidência |
|----------|------|--------|-----------|
| `POST /api/auth/login` | público | N/A | smoke + FIT-02 |
| `GET /api/health` | público | N/A | esperado |
| `GET /api/clientes` | sim | filtro por user | FIT-02 matrix |
| `GET /api/uploads` | sim | `validar_acesso_client_id` | FIT-02 cross-tenant |
| `POST` upload / delete upload | sim | S01-A | `test_s01a_*` |
| `GET /api/dados/todos` | sim | S01-A | `test_s01a_*` |
| produtividade mutável | sim | S01-A | `test_s01a_*` |
| clone / admin | admin | S01-A | `test_s01a_*` |
| `/api/ingestion/*` | dual lock | PR #4 bridge | flag off → 404; on → Bearer |

## Startup

| Checagem | Resultado |
|----------|-----------|
| Não altera tenant de usuários | OK (bloco removido S01-A) |
| Não redefine senha | OK |
| Não cria admin padrão com credencial | OK (`test_s01a_startup_*`) |
| `client_id=NULL` sem admin ≠ global | OK no guard `resolve_authorized_client` |
| Seeds startup | apenas configs não destrutivas |

## BLOCKERS — endpoints `/api/*` sem `get_current_*` (legado)

Varredura estática em `backend/main.py` (FIT-02): **~40** rotas `/api/*` sem dependency de autenticação.

### Críticos (bloqueadores de merge para produção)

| Método | Path | Risco |
|--------|------|-------|
| GET | `/api/clientes/{cliente_id}` | leitura de cadastro sem auth |
| POST | `/api/clientes` | criação sem auth |
| PUT | `/api/clientes/{cliente_id}` | alteração sem auth |
| POST | `/api/clientes/{cliente_id}/arquivar` | mutação sem auth |
| POST | `/api/clientes/{cliente_id}/ativar` | mutação sem auth |
| GET/POST/PUT | column-mapping / graficos config | mutação/leitura sem auth |
| GET | `/api/analises/*`, `/api/tendencias` | analytics sem auth |
| GET/POST/PUT/DELETE | `/api/dados*` (vários) | dados sem auth |
| GET | `/api/funcionario/perfil` | perfil sem auth |
| POST | `/api/upload/analyze`, `/api/upload/process` | upload pipeline sem auth |

> Nota: PR #4 protegeu um conjunto **crítico priorizado**, não a superfície completa. FIT-02 registra a dívida restante como **bloqueador de GO para merge/produção**.

## Ingestion auth

- Factory PR #4 wired via `backend/ingestion/pr4_bridge.py` + `wire_pr4_tenant_guard()` em `main.py`.
- Sem Bearer → 401; cross-tenant → 403; flag off → rotas não registradas (404).
