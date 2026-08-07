# Epic 2A — Master Handoff

## Baseline

PR #6 HEAD `9cd04147134581d5a7cde768b166cf8ed0e91b25`  
Branch: `feat/epic2a-biomed-performance-engine-shadow`  
PR #8 **not** used as base (documented).

## Delivered

- `backend/performance/*` shadow engine
- `scripts/shadow_performance_engine.py`
- ≥80 tests
- `docs/performance/*`
- Flag `ENABLE_BIOMED_PERFORMANCE_ENGINE=false`

## Future integration

1. Wire `MetricService.compute` → `MetricSnapshot` adapter  
2. Optional IQB from DataQualityService  
3. After UX/UI Epic 2 front: executive views only behind flags  
4. PR #4 when exposing any HTTP (not in 2A)

## Confirmations

No VPS/prod DB access; no real data; no user/auth changes; no merge/deploy.
