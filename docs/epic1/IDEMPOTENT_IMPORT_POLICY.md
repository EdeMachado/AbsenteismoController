# Idempotent Import Policy

1. Feature flag on  
2. Tenant/auth via adapter (PR #4-ready)  
3. Preview exists, confirmed, token valid, not consumed  
4. client/competência/file hashes unchanged vs preview  
5. Reupload identical classes blocked  
6. Idempotency key lookup → return prior success (`idempotent_hit`)  
7. Single transaction: raw meta + execution + canonical rows + line errors  
8. On error: full rollback; execution marked failed safely  

## Non-goals (this epic)

- No write to legacy `atestados`/`uploads`
- No delete/replace of prior competência
- No historical dedupe of production data
