# Epic 1 — Master Handoff

## Baseline

- Stacked on PR #6 HEAD `9cd04147134581d5a7cde768b166cf8ed0e91b25` (`feat/a02a-data-quality-shadow`)
- Branch: `feat/epic1-intelligent-data-ingestion`
- PR base: `feat/a02a-data-quality-shadow`
- PR #4 **not** included

## Delivered

- Full ingestion package + flag-gated API/UI
- ≥80 epic1 tests; A01/A02 100 tests preserved
- Docs under `docs/epic1/`
- Additive SQL up/down

## Integration with PR #4

1. Merge PR #4 to main (or integrate) when authorized  
2. Replace header bridge with session tenant dependency  
3. Set `PR4_TENANT_GUARD_FACTORY`  
4. Keep flag off until auth verified  

## Future merge order (proposal)

PR #4 → PR #5 → retarget/merge #6 → Epic1 → enable flag on staging only after backup.

## Activation checklist (later)

Backup → apply SQL on staging → flag on staging → smoke preview/import → monitor logs → only then consider prod (separate change window).

## Confirmations (this delivery)

- Production VPS not accessed  
- Production DB not touched  
- Users/passwords/`client_id`/permissions unchanged  
- No merge, no deploy  
- Real tenant PII not used in fixtures  
