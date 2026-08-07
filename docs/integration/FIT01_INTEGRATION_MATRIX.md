# FIT-01 — Matriz de Integração da Fundação

**Branch:** `integration/foundation-train`  
**Base:** `origin/main` @ `d0c012abaae9191531c3d2f30cb909407d31af01`  
**Escopo:** consolidação dos PRs #4, #5, #6, #8, #9 (docs), #10 — sem novas funcionalidades.

---

## Matriz completa

| PR | Objetivo | Arquivos (vs main) | Dependências | Conflitos | Risco | Feature Flag | Banco | Frontend | Backend | Testes | Rollback |
|----|----------|--------------------|--------------|-----------|-------|--------------|-------|----------|---------|--------|----------|
| **#4** | Auth + tenant guard S01-A | 11 (`main.py`, `tenant.py`, auth, clientes JS/HTML, testes) | `main` | Auto-merge limpo com main | **Alto** (segurança; toca rotas críticas) | N/A (sempre on no código do PR) | Não | Headers auth/compat (mínimo, do PR original) | `tenant.py`, guards em rotas | `test_s01a_*` | Reverter merge; legado sem guards |
| **#5** | Canonical Metrics shadow | 9 (`metric_service`, `shadow_compare`, docs, fixtures) | `main` | Nenhum vs #4 | Baixo | Shadow scripts (sem HTTP) | Não | Não | `backend/services/*` | `test_a01a_*` | Remover package services |
| **#6** | IQB / Data Quality shadow | +6 sobre #5 (15 vs main) | **#5** | Nenhum (fast-forward lineage) | Baixo–médio (metodologia) | Shadow | Não | Não | `data_quality_service.py` | `test_a02a_*` | Remover DQ service |
| **#8** | Intelligent Ingestion Epic 1 | 72 (package `ingestion`, SQL docs, UI experimental) | **#6** (+ espera guard #4 em runtime) | `main.py` ∩ #4 — **auto-merge OK** (ort manteve guards + registro flaggado) | Médio (SQL additive docs; flag off) | `ENABLE_INTELLIGENT_INGESTION=false` | SQL **documentado**, não auto-aplicado | `ingestion_experimental.*` (flag) | `backend/ingestion/*` + hook em `main.py` | `tests/ingestion/*` | Flag off; não aplicar SQL |
| **#9** | UX/UI + master architecture **docs** | 13 em `docs/master/` | docs architecture branch | Nenhum com código | Nenhum (docs) | N/A | Não | Não | Não | N/A | Remover docs |
| **#10** | Performance Engine 2A/2A-B | 60 (package `performance`, adapters, CLI) | **#6** (não #8) | `.env.example` ∩ #8 — **resolvido** unindo flags | Médio (metodologia/ROI) | `ENABLE_BIOMED_PERFORMANCE_ENGINE=false` | Não | Não | `backend/performance/*` | `test_epic2a*` / `test_epic2ab*` | Flag off; remover package |

---

## Sobreposições de arquivos (audit)

| Arquivo | PRs | Resolução na train |
|---------|-----|--------------------|
| `backend/main.py` | #4, #8 | Merge automático: guards S01-A + registro ingestion se flag true |
| `.env.example` | #8, #10 | União manual: ambas flags `=false` |
| `backend/services/*`, fixtures A01/A02, docs analytics | #5→#6→#8→#10 | Mesma linhagem a partir de #6; sem conflito de conteúdo |
| `docs/master/*` | #9 + doc Executive Intelligence | Adição documental na train |

---

## Ordem definitiva de integração

```text
origin/main
  → PR #4
  → PR #5
  → PR #6          (já baseado em #5; “retarget” implícito ao merge na train)
  → PR #8          (base #6; main.py com #4)
  → PR #10         (base #6; paralelo a #8; conflito só .env.example)
  → PR #9 docs + BIOMED_EXECUTIVE_INTELLIGENCE_ARCHITECTURE.md
```

**Justificativa:** a ordem proposta pelo pedido permanece correta.  
#10 **não** depende de #8 (merge-base comum = #6). Integrar #8 antes de #10 apenas reduz risco de conflito em `.env.example` e garante o hook de ingestion + tenant já presentes. Não há ordem melhor para segurança: #4 deve vir antes de qualquer superfície HTTP (#8).

---

## Duplicidades / adapters

- Fórmulas canônicas: uma fonte (`MetricService`); Performance usa adapters (não duplica).  
- IQB: `DataQualityService`; ingestion tem `iqb_adapter` thin.  
- Anti-PII: `shadow_compare` + `performance.privacy` + `ingestion.pii_mask` (escopos distintos; aceitável).  
- Tenant: `backend/tenant.py` (#4) + `ingestion/tenant_adapter.py` (fail-closed se #4 ausente).
