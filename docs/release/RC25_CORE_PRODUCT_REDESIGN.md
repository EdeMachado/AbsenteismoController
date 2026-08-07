# RC-25 — Core Product Redesign

**Status:** Code complete · **NÃO MERGEADO · NÃO DEPLOYADO**  
**Principle:** New visual composition on the same data/API base — not a CSS reskin of legacy DOM.

---

## What was rebuilt

| Surface | Route | New file | Legacy preserved |
|---------|-------|----------|------------------|
| Analytics | `/dashboard` (+ `/analytics` → redirect) | `analytics-core.html` + `analytics-core.js` | `/dashboard-legacy` → `index-legacy.html` |
| Empresas | `/clientes` | `empresas-core.html` + `empresas-core.js` | `/clientes-legacy` |
| Home | `/` | `index.html` + `home-core.js` | — (git history at `ad8b757`) |
| Apresentação | `/apresentacao` | `apresentacao-core.html` + `apresentacao-core.js` | `/apresentacao-legacy` |
| Funcionários | `/funcionarios` | `funcionarios-core.html` + `funcionarios-core.js` | old `funcionarios.html` unused by route |
| Upload | `/upload` | `upload-core.html` + `upload-core.js` | old `upload.html` unused by route |
| Comparativos | `/comparativos` | `comparativos-core.html` + `comparativos-core.js` | old file unused by route |
| Produtividade | `/produtividade` | `produtividade-core.html` + `produtividade-core.js` | old file unused by route |

Design system: `biomed-core.css` + `biomed-core.js`  
Components: PageHeader, MetricCard, ChartCard, Section, DataTable, FilterBar, EmptyState, LoadingState, ActionButton, entry/company cards, deck, heatmap, upload steps.

Shell cache: `rc25` · loads `biomed-core.css`.

---

## Metric source map (must not drift)

| KPI / chart | SOURCE_API | SOURCE_FIELD | CALCULATION |
|-------------|------------|--------------|-------------|
| Colaboradores | `/api/dashboard` | `metricas.funcionarios_afetados` | unchanged backend |
| Atestados | `/api/dashboard` | `metricas.total_atestados` \| `total_registros` | unchanged |
| Dias perdidos | `/api/dashboard` | `metricas.total_dias_perdidos` | unchanged |
| Horas perdidas | `/api/dashboard` | `metricas.total_horas_perdidas` | unchanged |
| Custo (quando houver) | `/api/dashboard` | `metricas.custo_estimado` | display only if > 0 |
| Frequência (display) | derived | `atestados / funcionarios_afetados` | ratio of existing fields |
| Duração média (display) | derived | `dias / atestados` | ratio of existing fields |
| Evolução | `/api/dashboard` | `evolucao_mensal.*` | unchanged |
| Setores | `/api/dashboard` | `top_setores.*` | unchanged |
| Centros de custo | `/api/dashboard` | `dias_centro_custo.*` | unchanged |
| Escalas | `/api/dashboard` | `top_escalas.*` | unchanged (proxy when cargo absent) |
| CID | `/api/dashboard` | `top_cids.*` | unchanged |
| Motivos | `/api/dashboard` | `top_motivos.*` | unchanged |
| Distribuição dias | `/api/dashboard` | `distribuicao_dias.*` | unchanged |
| Gênero | `/api/dashboard` | `distribuicao_genero.*` | unchanged |
| Recorrência | `/api/dashboard` | `frequencia_atestados.*` | unchanged |
| Heatmap | `/api/dashboard` | `heatmap_setores_meses.*` | unchanged |
| Produtividade chart | `/api/dashboard` | `produtividade.*` | unchanged |
| Comparativos | `/api/relatorios/comparativo` | `periodo1` / `periodo2` | unchanged |
| Produtividade list | `/api/produtividade` | `total`, `tipo_consulta` | unchanged |
| Produtividade evolução | `/api/produtividade/evolucao` | series `total` | unchanged |
| Empresas list | `/api/clientes` | client records | unchanged |
| Funcionários | `/api/dados/todos` (+ fallback `top_funcionarios`) | atestado rows | aggregation display only |
| Uploads histórico | `/api/uploads` | upload rows | unchanged |

No DB / API / business-rule changes.

---

## Screenshots

- BEFORE: `/opt/cursor/artifacts/rc25-before/`
- AFTER: `/opt/cursor/artifacts/rc25-after/`
- Capture script: `scripts/rc25_screenshots.py`

Surfaces: Dashboard, Empresas, Home, Apresentação, Funcionários, Upload, Comparativos, Produtividade (+ mobile dashboard/home).

---

## Explicit non-goals

- No Presentation Premium flag enable  
- No Intelligent Ingestion / Performance Engine  
- No merge / deploy / DB / API contract changes in this step  
- P0 tenant isolation fix remains separate (PR #39)

---

## Tests

`tests/release/test_rc25_core_product_redesign.py`  
Metric regression: OLD_VALUE (raw API fields) == NEW_VALUE (mapper) for atestados/dias/horas/funcionários; analytics JS binds chart SOURCE fields from `/api/dashboard`.
