# Epic 1 — Security Review

## Controls

| Control | Status |
|---------|--------|
| Feature flag default off | Yes |
| Dual lock: flag + PR #4 auth factory | Yes (fail-closed) |
| No parallel auth system | Yes — adapter for PR #4 only |
| **No browser identity headers** (`X-Ingestion-*`) | Yes — removed |
| Tenant from authenticated session/factory | Yes |
| Form `client_id` never identity source | Yes — validated against tenant |
| Global admin follows explicit PR #4-style policy | Yes (`is_global_admin`) |
| Path traversal on storage | Yes |
| Formula/macro rejection | Yes |
| Size/column/row limits | Yes |
| PII masked in preview | Yes |
| Logs without PII keys | Yes (`safe_log`) |
| No production path migrations | Yes |
| **No auto `/tmp` SQLite / no auto-schema on router** | Yes |
| Explicit `IngestionRepository` dependency | Yes |
| Legacy upload untouched | Yes |
| Confirmation token hashed | Yes |
| Cross-tenant preview blocked | Yes |

## Auth integration (PR #4)

```python
set_pr4_tenant_guard_factory(lambda request: Pr4Guard(request))
```

Without factory:

- mutable ingestion routes are **not registered** (even if flag is true);
- direct calls to `require_ingestion_tenant` fail closed → HTTP **503**.

Tests may set `INGESTION_ALLOW_TEST_DEPENDENCIES=true` and inject factory + repository.
Never enable that env in production.

## Persistence

- No `sqlite3.Connection` global in the router
- No `/tmp/absenteismo_epic1_experimental.db`
- No implicit `apply_epic1_schema` on request
- Use `set_ingestion_repository(...)` or explicit `INGESTION_SQLITE_PATH` (file must exist; schema applied offline)

## Residual risks

- Until PR #4 is merged and factory wired, experimental HTTP API stays dark (by design).
- `.xls` unsupported — operators must convert files.
- Staging path misconfiguration — refused for production-like paths; ops must migrate deliberately.

## Explicit non-actions

No VPS access, no prod DB, no user/password/`client_id` changes, no historical upload mutation, no Converplast/Roda de Ouro data correction in this PR.
