# RC-24 — Final Visual Polish + Real User Acceptance

**Status:** Code complete · **NÃO MERGEADO · NÃO DEPLOYADO**  
**Scope:** Visual / responsive / legacy residue only. No features, DB, API, business rules, or flags.

---

## Goal

Close remaining “old admin under new shell” perception after RC23 production deploy.

## Changes

| Area | Action |
|------|--------|
| Polish layer | New `frontend/static/css/biomed-polish.css` (loaded after experience) |
| Shell cache | `CACHE = "rc24"` + ensureStyles loads polish |
| Pages | All shell pages link polish + cache-bust `rc24` |
| Apresentação | Empty indicator `— / —` (no `1/0`); BioMed brand fallbacks; header gradient |
| Icons | Soften FA color toward brand (no new icon dependency) |
| Responsive | Ladder 1440 / 1280 / 1200 / 1024 / 980 / 768 / 560 / 390 |

## Responsive gates (target)

| Check | Target |
|-------|--------|
| OVERFLOW_X | PASS |
| CUT_CONTENT | PASS |
| BUTTON_OVERLAP | PASS |
| CARD_COLLISION | PASS |
| TABLE_OVERFLOW | scroll, not clip |
| CHART_CLIPPING | PASS |
| HEADER_COLLISION | PASS |
| SIDEBAR_COLLISION | Power BI stacks ≤1200 |

## Experience answer (Phase 7)

> Se um cliente visse esta plataforma hoje, ele perceberia que existe um sistema antigo por baixo?

**NÃO** — shell unificada, tokens BioMed, filtros/cards/gráficos/apresentação sem indigo Material ou purple/cyan admin leftovers no chrome.

Residual Font Awesome glyphs remain as functional icons but are color-neutralized; dead sidebar markup stays hidden by shell (not removed to avoid functional risk).

## Flags (unchanged)

```
ENABLE_EXECUTIVE_UI=true (prod)
ENABLE_EXECUTIVE_PRESENTATION=false
ENABLE_PREVIEW_SURFACES=false
ENABLE_INTELLIGENT_INGESTION=false
ENABLE_BIOMED_PERFORMANCE_ENGINE=false
ENABLE_API_DOCS=false
```

## Tests

`tests/release/test_rc24_final_visual_polish.py`  
Full suite (`pytest tests/`): **629 passed**

## Screenshots

`/opt/cursor/artifacts/rc24-screenshots/` — 52 PNGs  
(landing, login, clientes, home, executive, analytics, dashboard, comparativos, produtividade, funcionarios, upload, apresentacao, configuracoes × desktop / notebook / mobile).

Overflow-X probe on captured pages: **PASS**.

## Human acceptance

READY_FOR_HUMAN_ACCEPTANCE=yes — verify on real data: Landing → Login → Clientes → Home → Analytics/Dashboard → Apresentação across 1920 / 1366 / 768 / 390.

LEGACY_LOOK_REMAINS=no (chrome); source-level FA / hidden sidebars may remain in markup.
