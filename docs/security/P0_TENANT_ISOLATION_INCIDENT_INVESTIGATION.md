# P0 — CRITICAL TENANT ISOLATION INCIDENT
## Converplast × Roda de Ouro

**Status:** Root cause proven (investigation) · **NO FIX APPLIED · NO MERGE · NO DEPLOY**  
**Date:** 2026-08-07  
**Branch:** `cursor/p0-tenant-isolation-incident-f8f5`

---

## Delivery block

```
P0_TENANT_RESULT=GO
ROOT_CAUSE=FRONTEND_STALE_FETCH_RACE + MISNAMED_CHART_GATE + ADMIN_BROWSER_TENANT + OPTIONAL_CLONE_WRITE
CONVERPLAST_CLIENT_ID=2
RODA_DE_OURO_CLIENT_ID=4
AFFECTED_ENDPOINTS=(see below — API filters OK; UI/admin context contaminated)
AFFECTED_SCREENS=/dashboard (primary), /comparativos, /apresentacao, /produtividade (localStorage-driven); /clientes selection shell
DATA_ACTUALLY_CROSSED_TENANTS=no (API SQL read); yes_plausible (UI paint); possible (DB via clonar_dados)
METRICS_POTENTIALLY_CONTAMINATED=yes (if UI race or historical clone)
FIX_REQUIRED=yes
FILES_TO_CHANGE=frontend/static/js/dashboard.js; frontend/index-legacy.html; frontend/static/js/comparativos.js; backend/main.py (403→500 wrappers); optional clonar_dados governance
TEST_PLAN=tests/security/test_p0_tenant_isolation_bilateral.py (53 passed)
SECURITY_TESTS=bilateral sentinels + KPI SQL match + static race/gate proofs
READY_FOR_FIX=yes
```

---

## Tenant ID confirmation (not assumed)

| Tenant | client_id | Evidence |
|--------|-----------|----------|
| **Converplast** | **2** | `docs/integration/FIT07_FINAL_MERGE_GATE.md` (“Converplast (client_id=2)”); `docs/master/ABSENTEISMO_MASTER_ARCHITECTURE_IMPLEMENTATION_PLAN.md`; `atualizar_permissoes.py` (`client_id = 2  # CONVERPLAST`); dashboard JS `=== 2` |
| **Roda de Ouro** | **4** | FIT07 (“Roda de Ouro (client_id=4)”); master plan; dashboard/apresentacao JS `=== 4`; FIT07 notes Roda is **admin-accessible** |

---

## Auth / tenant chain (as implemented)

```
Login → JWT {sub: username} only
     → get_current_user / get_current_active_user
     → per-route client_id from Query/Form (browser localStorage.cliente_selecionado)
     → validar_acesso_client_id OR resolve_authorized_client
     → Analytics/SQL filter Upload.client_id == client_id
```

| Layer | Finding |
|-------|---------|
| JWT | **No tenant claim** |
| `/api/auth/me` | Returns user fields; **omits `client_id`** (proven by test) |
| Browser | `localStorage.cliente_selecionado` is sole active-tenant source for admin |
| Bound user | `current_user.client_id` enforced; foreign `client_id` → deny |
| Admin | May query **any** `client_id` sent by browser |

**Security rule gap vs target:** authenticated data APIs do validate user+requested client for bound users, but **admin tenant context is fully browser-trusted**. Fail-closed for missing client_id exists on `resolve_authorized_client`; some handlers still wrap 403 into **500**.

---

## Concrete root causes

### RC-1 — PRIMARY (UI contamination / “dados misturados” na tela)

**ENDPOINT:** `GET /api/dashboard?client_id={N}` (each call is tenant-filtered)  
**QUERY:** `Upload.client_id == client_id` via `Analytics.*` — **CLIENT_FILTER_MISSING=no**  
**FRONTEND_CONTEXT:**

```293:390:frontend/static/js/dashboard.js
async function carregarDashboard() {
    ...
    const response = await fetch(url);
    ...
    const data = await response.json();
    renderizarCards(data.metricas || {});
    setTimeout(() => {
        const secaoConverplast = document.getElementById('graficosConverplast');
        if (converplastClientId === 2) {
            secaoConverplast.style.display = 'block';
        } else {
            secaoConverplast.style.display = 'none';
        }
    }, 100);
    // renders charts from `data` with NO request generation / AbortController
}
```

**Proof:**
- `AbortController` **absent** in `dashboard.js` (static test).
- Overlapping fetches: request for client **2** can complete after shell already shows client **4** → paints Converplast KPIs/charts under Roda label (`cliente_selecionado_nome`).
- `#graficosConverplast` contains the **shared** main chart grid (`chartCids`, `chartEvolucao`, …) but is gated as if Converplast-only; hide is **deferred 100ms**.

**BACKEND_CONTEXT:** Not a SQL union of tenants.  
**CLIENT_FILTER_MISSING:** no (API) · **yes (UI request identity)**  

### RC-2 — Chart section mis-model (amplifies confusion)

**FILE:** `frontend/index-legacy.html`  
**STRUCTURE:** Main analytics canvases live inside `#graficosConverplast` (closed at “FIM GRÁFICOS CONVERPLAST”).  
For `client_id=4`, that entire grid is hidden; Roda sees `#graficosComparativos` + `#graficosRodaOuro` only.  
If hide fails or races, operator sees “Converplast” section with whatever payload last painted.

### RC-3 — Admin browser-only tenant (systemic)

**FRONTEND_CONTEXT:** `getCurrentClientId()` ← `localStorage.cliente_selecionado`  
**BACKEND_CONTEXT:** Admin bypass in `validar_acesso_client_id` / `resolve_authorized_client`  
FIT07: Roda operated by **administrators** (no bound tenant user). Any stale/wrong localStorage immediately selects the wrong tenant for all admin data calls.

### RC-4 — Physical DB copy (optional / historical)

**ENDPOINT:** `POST /api/clientes/{cliente_id}/clonar_dados?origem_id=`  
**QUERY:** reads `Upload` where `client_id == origem_id`, writes new rows with `client_id == destino.id`  
**CLIENT_FILTER_MISSING:** N/A (intentional cross-tenant **write**)  
If Converplast→Roda clone was ever run, Roda’s DB contains Converplast *content* under `client_id=4`. Subsequent “correct” filters still show that content as Roda’s.

### RC-5 — Comparativos fallback to `client_id=1`

**FILE:** `frontend/static/js/comparativos.js`  
`getCurrentClientId(1)` / `|| 1` — if selection missing, requests tenant **1** (not 2/4). Wrong-tenant risk, not the Converplast↔Roda mix itself.

### RC-6 — 403 swallowed as 500 (secondary)

**ENDPOINTS:** e.g. `/api/apresentacao`, `/api/produtividade/evolucao`, `/api/dashboard` (on some paths)  
Catch `HTTPException` and re-raise as 500 with message containing “403: Acesso negado…”.  
Data still withheld; status fail-closed violated.

---

## What was NOT found

- No analytics path that runs `.query(Atestado).all()` without `Upload.client_id` join/filter on `/api/dashboard`.
- No module-level Python cache merging Converplast+Roda dashboard payloads.
- Bound user (`client_id=2`) **cannot** successfully read Roda endpoints (bilateral tests: deny).

---

## Bilateral sentinel test results

`tests/security/test_p0_tenant_isolation_bilateral.py` — **53 passed**

| Check | Result |
|-------|--------|
| Converplast user → Roda endpoints | DENIED |
| Roda user → Converplast endpoints | DENIED |
| Converplast payload contains `CONVERPLAST_SENTINEL`, not `RODA_DE_OURO_SENTINEL` | PASS |
| Roda payload contains `RODA_DE_OURO_SENTINEL`, not `CONVERPLAST_SENTINEL` | PASS |
| Admin query per tenant excludes foreign sentinel | PASS |
| Dashboard `total_dias_perdidos` == SQL `sum(dias)` filtered by tenant | PASS |
| Static proof of race / Converplast gate / comparativos `|| 1` | PASS |

---

## Affected surfaces

| Screen | Risk |
|--------|------|
| `/dashboard` | **HIGH** — race + Converplast-named shared grid |
| `/comparativos` | MEDIUM — fallback `client_id=1`; localStorage reload without abort |
| `/apresentacao` | MEDIUM — localStorage-driven; admin context |
| `/produtividade`, `/funcionarios`, `/upload*`, Power BI, Executive | MEDIUM — same browser tenant source for admin |
| `/clientes` → Entrar | Sets `cliente_selecionado`, redirects `/` |

---

## Metrics contamination

| Source | Contaminated? |
|--------|----------------|
| API KPIs for a single correct `client_id` | **No** (matches tenant SQL in tests) |
| On-screen KPIs during admin tenant switch | **Yes, potentially** (stale fetch) |
| KPIs if clone copied Converplast→Roda | **Yes** (data now belongs to destination tenant) |

Revalidate production metrics only **after** UI race fix + SQL audit for cloned/orphan content.

---

## Fix plan (NOT executed in this step)

1. **dashboard.js:** request generation token / `AbortController`; ignore stale responses; hide/show chart sections **synchronously** before paint.  
2. **index-legacy.html:** rename/split shared chart grid from “Converplast-only” gate; Roda must see shared analytics under neutral container.  
3. **comparativos.js:** remove `client_id=1` fallback; fail closed.  
4. **backend:** stop wrapping tenant `HTTPException` into 500; always 403.  
5. **governance:** restrict/audit `clonar_dados`; prod SQL check for sentinel-like cross copies.  
6. **optional hardending:** bind active tenant server-side for admin sessions (not browser-only).

---

## Incident answers (required shape)

```
ENDPOINT=/api/dashboard (read OK) + frontend carregarDashboard (paint race)
QUERY=Analytics → join Upload.filter(Upload.client_id == client_id)  # present
CLIENT_FILTER_MISSING=no (SQL) / yes (UI in-flight identity)
FRONTEND_CONTEXT=localStorage.cliente_selecionado + no AbortController + deferred #graficosConverplast hide
BACKEND_CONTEXT=admin may use any client_id; JWT has no tenant; /api/auth/me omits client_id
```

---

## Explicit non-actions

- No production deploy  
- No merge of fix (investigation only)  
- No feature / metric formula / DB schema changes in this PR  
