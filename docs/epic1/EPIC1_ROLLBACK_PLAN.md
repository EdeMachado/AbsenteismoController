# Epic 1 — Rollback Plan

## Code rollback

1. Keep `ENABLE_INTELLIGENT_INGESTION=false` (default)  
2. Or revert merge of this branch  
3. Legacy upload continues unaffected  

## Schema rollback (only if additive tables were applied somewhere)

1. Backup  
2. Run `001_epic1_ingestion_down.sql`  
3. Verify legacy tables/row counts intact  
4. Smoke legacy `/api/upload` + dashboard  

## Data

Epic1 import does not mutate legacy atestados — rolling back epic1 tables does not require restoring production event data for this feature path.

## Forbidden

No production execution in this delivery. No deploy. No merge without explicit human approval.
