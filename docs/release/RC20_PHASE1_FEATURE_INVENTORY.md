# RC-20 Phase 1 — Feature Inventory (mandatory addendum)

**Status:** COMPLETE (code-verified)  
**Rule:** No invented modules. Menu and migration maps only reference routes/APIs that exist.  
**Date:** 2026-08-07

---

## LEGACY_FEATURE_INVENTORY

### Pages with real UI + real APIs

| Module | Route | File | KPIs / charts / tables / filters |
|---|---|---|---|
| Dashboard operacional | `/dashboard` | `index-legacy.html` + `dashboard.js` | Filtros período/funcionário/setor; dias/horas perdidas; TOP CIDs; evolução mensal; TOP setores; gênero; dias por doença; escalas; motivos; centro de custo; distribuição dias; comparativos mensal/trimestral/ano; heatmap; produtividade (charts); Roda de Ouro (client-specific); alertas; filtros salvos |
| Clientes / Empresas | `/clientes` | `clientes.html` | Snapshot clientes ativos/arquivo/sem dados; CRUD; logos; cores; mapeamento colunas; clonagem |
| Upload planilha | `/upload` | `upload.html` | Dropzone; histórico uploads; mês/ano referência |
| Meus Dados (registros) | `/dados_powerbi` | `dados_powerbi.html` | Grid editável atestados; filtros ano/mês/busca; tendência; export |
| Funcionários | `/funcionarios` | `funcionarios.html` | KPIs médias; tabela; filtros; edição gênero massa; export |
| Perfil funcionário | `/perfil_funcionario` | `perfil_funcionario.html` | KPIs atestados/dias/horas; evolução; TOP CIDs; histórico |
| Comparativos | `/comparativos` | `comparativos.html` | Período 1 vs 2; variações; gráfico comparação |
| Produtividade | `/produtividade` | `produtividade.html` | Consolidado mensal por categoria (ocupacionais, assistenciais, acid. trabalho, INSS, sinistralidade, absenteísmo…); CRUD |
| Dashboard Power BI style | `/dashboard_powerbi` | `dashboard_powerbi.html` | KPIs registros/dias/horas/taxa; 6 charts; filtros depto/tipo/ano/mês |
| Apresentação (legado) | `/apresentacao` | `apresentacao.html` | Deck slides + export PPTX via `/api/apresentacao` |
| Configurações | `/configuracoes` | `configuracoes.html` | Config sistema; users admin |
| Upload inteligente | `/upload_inteligente` | `upload_inteligente.html` | Analyze/process (`/api/upload/analyze`, `/process`) |
| Auto processor | `/auto_processor` | `auto_processor.html` | Pipeline auto |
| Auth | `/login` | `login.html` | `/api/auth/login` |

### Legacy menu (`menu.js` — labels reais)

Dashboard · Clientes · Apresentação · Upload Planilha · Meus Dados · Produtividade · Funcionários · Comparativos · Configurações

### Stub / orphan (exist but incomplete)

| Item | Route / file | Status |
|---|---|---|
| Análises | `/analises` | Stub “em desenvolvimento” — **no UI charts** |
| Tendências | `/tendencias` | Stub — **no UI charts** |
| Preview dados | `/preview` | Stub page (legacy upload-preview HTML exists separately) |
| Relatórios | `/relatorios` | Route **commented out** in `main.py` |
| INSS | `inss.html` only | **No HTML route; no `/api/inss*`** — NOT_AVAILABLE as product surface |
| Landing legado | `landing-legacy.html` | Preserved in git; not public route |

### Legacy APIs (REAL)

`/api/dashboard`, `/api/filtros`, `/api/filtros-salvos*`, `/api/alertas`, `/api/clientes*`, `/api/upload(s)`, `/api/dados*`, `/api/analises/{funcionarios,setores,cids}`, `/api/tendencias`, `/api/relatorios/comparativo`, `/api/produtividade*`, `/api/funcionario/*`, `/api/apresentacao`, `/api/export/{excel,pptx}`, `/api/config*`, `/api/users*`, `/api/auth*`

Note: `/api/analises/setores|cids` and `/api/tendencias` exist but stub pages do not consume them.

---

## NEW_FEATURE_INVENTORY

| Surface | Route | Status |
|---|---|---|
| Landing premium | `/landing` | Production-safe BioMed landing (RC-20) |
| Login BioMed | `/login` | Reskin; same auth contract |
| Platform Hub | `/` | Module cards + shell |
| Unified shell | `biomed-platform-shell.js` | Overlay on hub + legacy pages |
| Visão Executiva | `/executive` | First → Decision → Evidence (`app-first.js`) |
| Executive Presentation | `/executive/presentation` | **OFF** (`ENABLE_EXECUTIVE_PRESENTATION`) |
| Preview landing/ficha/presentation | `/preview/*`, `/f/*` | **Blocked in production** |
| Ficha digital | APIs `/api/preview/ficha*` | PREVIEW_ONLY |
| Executive APIs | `/api/executive/*` | Behind `ENABLE_EXECUTIVE_UI` |

### Executive live UI (subset of aggregate)

- KPIs abertura: horas perdidas, dias perdidos, custo (com estado), Executive Score  
- Decision: mini-bars setores / Pareto CID / evolução  
- Evidence: fontes, timeline, IQB, confiança, limites  
- **Not wired in live HTML:** `app.js`, `charts.js`, `analytics.js`, full Chart.js command-center (exist on disk)

---

## MISSING_IN_NEW

Content that existed in legacy and was **not reachable / not visible** in the early thin shell / Executive-only perception:

1. Dashboard operacional completo (`/dashboard`) — dezenas de gráficos  
2. Comparativos período a período  
3. Meus Dados / grid de atestados  
4. Dashboard Power BI style  
5. Produtividade CRUD  
6. Funcionários + perfil  
7. Upload + upload inteligente  
8. Clientes CRUD completo  
9. Apresentação legada + PPTX  
10. Alertas / filtros salvos (dentro do dashboard)  
11. Charts legado não espelhados no Executive live: gênero, escalas, motivos, top funcionários (privacy), produtividade, heatmap detalhado, dual-period custom  

**Root cause of “só 2 módulos”:** Executive live UI is intentionally a CEO subset; Analytics parent previously pointed at stub `/analises`; shell initially under-linked real legacy analytics routes.

---

## DATA_SOURCE_MAP

| Surface / field | SOURCE |
|---|---|
| Dashboard `/api/dashboard` series | REAL (DB) |
| Meus Dados / funcionários / uploads | REAL |
| Comparativos `/api/relatorios/comparativo` | REAL |
| Produtividade `/api/produtividade*` | REAL |
| Apresentação `/api/apresentacao` | REAL |
| Executive eventos/dias/setores/CID/série | REAL (`MetricService`) |
| Executive horas estimadas / cobertura estimada | ESTIMATED |
| Executive custo `estado=REAL` | REAL |
| Executive custo `estado=ESTIMADO` | ESTIMATED |
| Executive custo `estado=ILUSTRATIVO` | ILLUSTRATIVE (staging demo only) |
| Executive custo não informado | NOT_AVAILABLE |
| Executive Score / IQB | REAL when computable; else NOT_AVAILABLE |
| BioMed Performance Engine (prod default) | NOT_AVAILABLE |
| ROI executive | NOT_AVAILABLE (`ROI_NAO_CALCULAVEL`) |
| Preview presentation deck | ILLUSTRATIVE |
| Ficha digital | PREVIEW / in-memory — not production persistence |
| INSS module | NOT_AVAILABLE (no API) |
| `/analises`, `/tendencias` pages | NOT_AVAILABLE (stubs) |

**Rule RC-20:** no mock numbers on production surfaces without SOURCE marker.

---

## GRAPH_INVENTORY

### Legacy (`/dashboard` + related)

TOP CIDs · Evolução mensal · TOP setores · Gênero · Dias por doença · Dias/funcionários · Evolução setor · Escalas · Motivos · Centro de custo · Distribuição dias · Média CID · Setor×gênero · Dias vs horas · Frequência atestados · Produtividade (múltiplos) · Comparativos mensal/trimestral/ano · Heatmap · Roda de Ouro (client 4) · Converplast-specific (client 2)

### Executive live

Mini-bars only: setores · pareto_cid · evolucao_temporal (+ scoreboard KPIs)

### Executive API (built, mostly unused by live page)

Same as above + centro_custo + custo_* + dia_semana + cargo when available

---

## TARGET_MENU

Based **only** on verified routes (no invented “Causas/Setores” pages — those live inside Visão Geral):

```
Início                         → /
Visão Executiva                → /executive
Analytics
  Visão Geral                  → /dashboard          (REAL charts)
  Comparativos                 → /comparativos
  Dados / Power BI             → /dados_powerbi
  Dashboard Power BI           → /dashboard_powerbi
  Produtividade                → /produtividade
Operacional
  Clientes / Empresas           → /clientes
  Uploads                      → /upload
  Upload inteligente           → /upload_inteligente
  Funcionários                 → /funcionarios
Apresentação                   → /apresentacao
Fichas                         → disabled (PREVIEW_ONLY)
Configurações                  → /configuracoes
```

**Explicitly excluded from menu until real:** `/analises`, `/tendencias` (stubs), INSS (orphan), `/executive/presentation` (OFF), Relatórios (removed).

---

## FEATURE_MIGRATION_MAP

| Legacy capability | Destination in One Platform |
|---|---|
| Dashboard charts/filtros/alertas | Analytics → Visão Geral (`/dashboard`) |
| Comparativos | Analytics → Comparativos |
| Meus Dados + Dashboard PB | Analytics → Dados / Power BI |
| Produtividade | Analytics (also ops workflow) → Produtividade |
| Clientes | Operacional |
| Upload / upload inteligente | Operacional |
| Funcionários / perfil | Operacional |
| Apresentação PPTX | Apresentação |
| Config / users | Configurações |
| CEO narrative / score / decision | Visão Executiva |
| Ficha digital | Blocked until flag |
| Presentation premium | Blocked until flag |

---

## EXECUTIVE_KEEP

- Opening / Decision / Evidence journey  
- Aggregate KPIs (dias, horas, custo com estados, score, IQB)  
- Privacy (no worker ranking / PII)  
- Baseline trend + decision narrative  
- Optional presentation deck (flagged OFF)

## ANALYTICS_MOVE

- Full Chart.js / dashboard depth  
- Comparativos dual-period  
- Meus Dados / Power BI views  
- Produtividade charts + consolidado  
- Aggregate-safe CID/setor/CC detail beyond executive mini-bars  
- Future: wire catalog `/api/executive/analytics` into Analytics UX (not into Opening)

## OPERATIONS_MOVE

- Clientes CRUD  
- Uploads + intelligent upload  
- Funcionários + perfil nominal  
- Produtividade data entry  
- Fichas (when unblocked)  
- Configurações / users  

---

## Inventory completeness checklist

- [x] All routed HTML pages inventoried  
- [x] Legacy menu.js labels captured  
- [x] Stub/orphan modules declared NOT_AVAILABLE  
- [x] Executive live vs API vs unwired modules separated  
- [x] SOURCE tags for major surfaces  
- [x] TARGET_MENU only uses real routes  
- [x] Migration keep/move classifications  

**INVENTORY_COMPLETE=yes**
