# RC-1.6 — Controlled Merge Report

**Status:** Merge to `main` completed · **DEPLOY NÃO EXECUTADO** · VPS não acessado  
**Date (UTC):** 2026-08-07

---

## Baseline / merge identity

| Field | Value |
|-------|-------|
| PR autorizado | [#25](https://github.com/EdeMachado/AbsenteismoController/pull/25) |
| PR25 HEAD (antes) | `edb0f9a89fb31b3ad408275f4bfc200dd1f2c258` |
| Base branch | `main` |
| MAIN_BEFORE_MERGE | `540cda0806326aa14ced57d42fd43e8a69817d08` |
| MERGE_COMMIT | `9ed88591f08a5261abb09d7d9e03493a52dff2c3` |
| MAIN_AFTER_MERGE | `9ed88591f08a5261abb09d7d9e03493a52dff2c3` |
| Merge method | **merge commit** (não squash) |
| Parents | `540cda08…` + `edb0f9a…` |
| RC tip ancestral de main | YES |

---

## Pre-merge validation

| Check | Result |
|-------|--------|
| PR25_STATE | OPEN → READY → MERGED |
| PR25_HEAD | `edb0f9a…` (match esperado) |
| PR25_BASE | `main` |
| PR25_MERGEABLE | true |
| MAIN_HEAD pré-merge | `540cda08…` (match esperado) |
| Foundation CI (PR #25 / HEAD) | **SUCCESS** ([run 31190310057](https://github.com/EdeMachado/AbsenteismoController/actions/runs/31190310057)) |
| Local `pytest -q tests/` | **548 passed** |
| `compileall backend` | PASS |
| `import backend.main` | PASS |

---

## Gate (reconfirmado pré-merge)

| Item | Value |
|------|-------|
| PREVIEW_ROUTES_PRODUCTION_BLOCKED | yes (`ENVIRONMENT=production` → 404 em `/preview/*`, `/staging/*`, `/api/preview/ficha/*`, `/f/*`) |
| Legacy `/preview` | preservado (upload preview) |
| DIGITAL_FORM_STATUS | PREVIEW_ONLY (in-memory) |
| MIGRATION_REQUIRED / EXECUTED | no / no |
| FLAGS_DEFAULT_OFF | yes (`ENABLE_EXECUTIVE_UI`, `ENABLE_EXECUTIVE_PRESENTATION`, `ENABLE_INTELLIGENT_INGESTION`, `ENABLE_BIOMED_PERFORMANCE_ENGINE`, `ENABLE_API_DOCS`, `ENABLE_PREVIEW_SURFACES`) |
| SECURITY_GATE | GO |

---

## Post-merge validation

| Check | Result |
|-------|--------|
| `origin/main` | `9ed88591f08a5261abb09d7d9e03493a52dff2c3` |
| `edb0f9a…` ancestral | YES |
| GitHub Actions em push `main` | **não dispara** (workflow só: `pull_request`→main, `push`→`integration/foundation-train`, `workflow_dispatch`) |
| `workflow_dispatch` | HTTP 403 (token sem permissão) |
| Reprodução local Foundation + full suite no tip `9ed8859` | FIT suite **55 passed**; full **548 passed**; compile/import PASS |
| POST_MERGE_CI (equivalente local) | PASS |
| Deploy | **não executado** |

---

## PRs superseded (fechados sem merge independente)

Comentário em cada um:

> SUPERSEDED by PR #25 / RC-1.5 final release gate.  
> No independent merge required.

PRs: **#13, #14, #15, #16, #17, #18, #19, #20, #21, #22, #23, #24**

Branches **não** excluídas nesta etapa.

---

## Decisão final

**RC16_RESULT=GO** (merge controlado concluído)

**NÃO iniciar deploy.**  
Flags permanecem OFF. Ficha Digital permanece PREVIEW_ONLY. Sem migration. Sem alteração de `.env` / VPS / Hostinger.

### NEXT_ACTION

Planejar etapa de deploy/homologação **separada** (backup + procedimento explícito), somente após autorização humana. Não ativar flags experimentais.
