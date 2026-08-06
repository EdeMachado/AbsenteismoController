# Epic 1 — Security Review

## Controls

| Control | Status |
|---------|--------|
| Feature flag default off | Yes |
| No parallel auth system | Yes — adapter for PR #4 |
| Tenant mismatch blocked | Yes |
| Path traversal on storage | Yes |
| Formula/macro rejection | Yes |
| Size/column/row limits | Yes |
| PII masked in preview | Yes |
| Logs without PII keys | Yes (`safe_log`) |
| No production path migrations | Yes (`MigrationNotAllowedError`) |
| Legacy upload untouched | Yes |
| Confirmation token hashed | Yes |
| Cross-tenant preview blocked | Yes |

## Residual risks

- Header auth bridge (`X-Ingestion-*`) is temporary until PR #4 dependency injection; must not be exposed without reverse-proxy auth in any future activation.
- Experimental temp DB under OS temp dir — only when flag on and API used; not production DB.
- `.xls` unsupported — operators must convert files.

## Explicit non-actions

No VPS access, no prod DB, no user/password/`client_id` changes, no historical upload mutation, no Converplast/Roda de Ouro data correction in this PR.
