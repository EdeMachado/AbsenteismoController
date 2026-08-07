# P0 — Multitenant isolation incident investigation

**Repo:** AbsenteismoController / BioMed Platform  
**Scope:** Converplast (`client_id=2`) vs Roda de Ouro (`client_id=4`) reported data mixing  
**Method:** Static code audit (auth, tenant deps, queries, frontend client context, tests)  
**Date:** 2026-08-07  

---

## Verdict (short)

Backend SQL paths for atestados/uploads/produtividade **do filter by `client_id`**. There is **no** evidence in code of a query that returns both tenants’ rows in one response.

The **most likely root cause of the reported “mixed data” symptom** is **admin tenant context owned by `localStorage.cliente_selecionado`**, combined with **dashboard fetch races / deferred UI hide**, not a missing `Upload.client_id == …` filter on `/api/dashboard`.

**`DATA_ACTUALLY_CROSSED_TENANTS` cannot be proven from code alone** (would require prod DB inspection or evidence that `/api/clientes/{id}/clonar_dados` / wrong-client upload was used).

---

## 1. Auth / tenant dependency graph

```
Browser
  ├─ localStorage.access_token          → Bearer JWT
  ├─ localStorage.cliente_selecionado   → query/body/Form client_id  (NO X-Client-Id header)
  └─ localStorage.user                  → {id, username, is_admin}  (NO client_id field)

HTTP
  └─ api_auth_middleware (backend/main.py)
        • Requires Bearer on non-public /api/*
        • Decodes JWT `sub` = username only
        • Loads User from DB → request.state.current_user
        • Does NOT resolve or bind tenant

Route Depends
  ├─ get_current_user / get_current_active_user  (backend/auth.py)
  │     JWT → User (username). Claims: {sub, exp} only. No client_id claim.
  ├─ get_current_admin_user / require_admin_user
  │     is_admin == True
  └─ Tenant assert (one of):
        • resolve_authorized_client(db, user, requested)   (backend/tenant.py)  [preferred]
        • validar_acesso_client_id(user, client_id)        (backend/main.py)
        • require_tenant_client / assert_tenant_access     (backend/authz.py)
        • validar_client_id(db, client_id)                 EXISTS ONLY — not membership

resolve_authorized_client rules (S01-A):
  • user.client_id set     → must match requested (else 403); authorized = user.client_id
  • is_admin + client_id NULL → requested required; any existing client OK
  • client_id NULL + not admin → 403
  • no silent fallback to client_id=1
```

### Client selection (frontend)

| Mechanism | Used? | Notes |
|-----------|-------|-------|
| `localStorage.cliente_selecionado` | **Yes — primary** | Set in `frontend/static/js/clientes.js` `salvarSelecaoCliente` |
| `getCurrentClientId()` | Yes | `frontend/static/js/auth.js` — reads localStorage only |
| Query `?client_id=` | Yes | Almost all business GETs |
| Form `client_id` | Yes | Upload / produtividade POST |
| Header `X-Client-Id` | **No** | Not implemented |
| JWT claim `client_id` | **No** | Login token is `{"sub": username, "exp": …}` |
| `/api/auth/login` / `/api/auth/me` return `client_id` | **No** | Cannot reconcile bound tenant from API user payload |

Production access model (FIT-07 inventory): Converplast has 1 bound user; **Roda de Ouro is admin-accessible**. Admins (`is_admin=True`, typically `client_id=NULL`) may open either tenant by changing localStorage and sending that id.

---

## 2. AFFECTED_ENDPOINTS

Legend:

- **CLIENT_FILTER_MISSING** = query can return another tenant’s rows / no tenant assert  
- Membership for **bound** users is enforced where noted; **admin** may access any client by design

| Endpoint | CLIENT_FILTER_MISSING | Why |
|----------|----------------------|-----|
| `GET /api/dashboard` | **no** | `validar_client_id` + `validar_acesso_client_id`; Analytics always `Upload.client_id == client_id` |
| `GET /api/apresentacao` | **no** | Same; slides branched `if client_id == 2` / `elif client_id == 4` after filter |
| `GET /api/dados/todos` | **no** | `resolve_authorized_client` + join filter |
| `GET /api/produtividade` (+ evolucao/POST) | **no** | `resolve_authorized_client` + `Produtividade.client_id` |
| `GET /api/uploads`, `DELETE /api/uploads/{id}` | **no** | Filter + ownership on upload |
| `GET/PUT/DELETE /api/dados/{atestado_id}` | **no** | Derive tenant from upload; `validar_acesso_client_id` |
| `POST /api/upload` | **no** | `resolve_authorized_client` then write with that id |
| `POST /api/upload/process` | **no** | `validar_*` pair |
| `GET /api/filtros`, `/api/alertas`, `/api/analises/*`, `/api/tendencias`, `/api/export/*`, `/api/relatorios/comparativo`, `/api/funcionario/perfil` | **no** | Tenant assert + client-scoped queries |
| `GET /api/clientes` | **no** (scoped) | Admin=all; bound=own; orphan=403 |
| `POST /api/clientes/{id}/clonar_dados` | **intentional cross-tenant WRITE** | Admin copies uploads+atestados origem→destino. Can **physically** place Converplast rows under Roda’s `client_id` |
| `PUT/DELETE /api/filtros-salvos/{filtro_id}`, `GET …/aplicar` | **partial** | Scoped by `user_id` only, **not** re-checked against selected `client_id`. Admin filters saved under tenant A can be applied while UI shows tenant B (name lists leak; not full event dump) |
| `POST /api/upload/analyze` | **n/a (no tenant data)** | Auth only; no `client_id`; analyzes temp file |
| `GET /api/executive/*` (when flag on) | **no** | `_resolve_client_id` → `resolve_authorized_client` |
| `GET /api/executive/health` | **no tenant data** | Unauthenticated health stub |
| `GET /api/notifications` | **global process memory** | Admin-only; `notification_service` module list — not client-scoped business data |

**Historical (fixed in tree, still relevant to incident narrative):** FIT-04 notes `/api/export/excel|pptx` previously used **only** `validar_client_id` (existence) → authenticated cross-tenant read. Now uses `resolve_authorized_client`.

---

## 3. Global / cross-tenant state

| Location | Risk |
|----------|------|
| `backend/cache_service.py` `cache_service` | Process-global dict; keys *can* include client_id prefix helpers, but **not** wired as primary dashboard cache path today |
| `backend/notification_service.py` `notification_service` | Process-global list of admin notifications |
| `rate_limit_store` in `main.py` | IP-keyed, not tenant data |
| `frontend` `window.alertasData`, Chart.js `window.chart*` | **Can show previous tenant** if a late fetch finishes after switch |
| `localStorage.cliente_selecionado` (+ nome/tema/logo) | Shared across tabs; sole client context for admins |
| `comparativos.js` | **`getCurrentClientId(1)` / `\|\| 1` fallback** — can call API with `client_id=1` if selection missing |

No module-level Python dict was found that stores Converplast+Roda analytics payloads keyed without tenant.

---

## 4. Hardcoded Converplast / Roda (`2` / `4`)

Appears extensively as **theme / slide / section branching**, not as SQL “OR client_id IN (2,4)”:

- `frontend/static/js/auth.js` — sidebar classes for id 2 / 4  
- `frontend/static/js/dashboard.js` — show `#graficosConverplast` iff `=== 2`; `#graficosRodaOuro` iff `=== 4`  
- `frontend/static/js/apresentacao.js` — RO branding  
- `backend/main.py` — apresentação slide trees `if client_id == 2` / `elif client_id == 4`  
- Tests/docs/seeds use synthetic ids 2 and 4 aligned to production  
- `docs/executive/EXEC01_BASELINE_SNAPSHOT.md`: production clients **2 CONVERPLAST · 4 RODA DE OURO**  
- Dead script `atualizar_permissoes.py` (exits 2): historically set Nilceia→2 and **everyone else `client_id=NULL` (“acesso a todos”)** — dangerous old semantics; S01-A disabled mass clear

`#graficosConverplast` in `frontend/index-legacy.html` is **misnamed**: it holds the **shared** chart grid (TOP CIDs, evolução, etc.), default **visible** (no `display:none`). Hide for non-2 is deferred `setTimeout(..., 100)` in `dashboard.js`. Roda-specific block starts hidden.

---

## 5. Test gaps (`tests/test_s01a_tenant_guard.py` + FIT-04)

Covered well:

- `resolve_authorized_client` bound/orphan/admin/missing  
- Cross-tenant 403 on `/api/produtividade`, `/api/dados/todos`  
- List clientes scoped  
- No fallback when `client_id` omitted on produtividade  

Gaps vs this incident:

- **No** isolation race test for `/api/dashboard` + client switch  
- **No** assert that dashboard response payload never contains both tenants’ identifiers  
- FIT-04 concurrency test is **sequential** HTTP only (comment: SQLite not thread-safe) — does not model overlapping browser fetches  
- **No** test that `comparativos.js` must not fallback to `1`  
- Clone tested admin-only; not “clone then dashboard still labeled correctly”  
- Auth `/me` not asserted to expose `client_id` for bound users  

---

## 6. Most likely ROOT_CAUSE (with evidence)

### Primary (perceived mixing for admin operators)

**Tenant context is client-controlled via `localStorage`, not JWT; dashboard loads are not request-sequenced.**

Evidence:

```45:48:frontend/static/js/auth.js
function getCurrentClientId(defaultId = null) {
    const stored = Number(localStorage.getItem('cliente_selecionado'));
    return Number.isFinite(stored) && stored > 0 ? stored : defaultId;
}
```

```1027:1039:backend/main.py
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        ...
        "user": {
            "id": user.id,
            "username": user.username,
            ...
            "is_admin": user.is_admin
        }
    }
```

```293:355:frontend/static/js/dashboard.js
async function carregarDashboard() {
    ...
    limparTodosDadosDashboard();
    ...
    let url = `/api/dashboard?client_id=${clientId}`;
    ...
    const response = await fetch(url);
    ...
    const data = await response.json();
    // paints charts with `data` — no generation token / AbortController
```

If request A (Converplast) completes after user switched to Roda and started request B, **A’s payload paints under the Roda shell label**. That matches “data from Converplast and Roda mixed” without any SQL union.

Additionally, `#graficosConverplast` stays visible until a 100ms timeout hides it for non-2 clients — brief dual-section flash possible when switching.

### Secondary (real DB cross-tenant if used)

```2401:2451:backend/main.py
@app.post("/api/clientes/{cliente_id}/clonar_dados")
...
        require_admin_user(current_user)
        ...
        for upload in uploads_origem:
            novo_upload = Upload(
                client_id=destino.id,
                ...
            )
```

Admin clone **copies** origem events into destino under destino’s `client_id`. Subsequent filtered queries are “correct” per tenant id but content is the other company’s.

### Tertiary (wrong tenant id from frontend)

```8:8:frontend/static/js/comparativos.js
    const clientId = ... getCurrentClientId(1) : (... || 1);
```

Falls back to **`client_id=1`** (not 2/4). Can load empty/wrong tenant if selection missing — violates project “no fallback to 1” policy on the client side.

### What is NOT the root cause (from this audit)

- Missing `Upload.client_id` filter inside `backend/analytics.py` metric methods (they consistently filter).  
- Unauthenticated open business APIs (FIT-03 middleware + Depends).  
- JWT forging of `client_id` (claim does not exist).  

---

## 7. `DATA_ACTUALLY_CROSSED_TENANTS`?

| Question | Answer from code alone |
|----------|------------------------|
| Can one HTTP response include both tenants’ atestado rows via a missing filter? | **No evidence** |
| Can UI show Converplast metrics while shell says Roda (or reverse)? | **Yes — race / stale fetch / deferred hide** |
| Can DB permanently hold Converplast content under `client_id=4`? | **Yes — only via admin clone or admin upload with wrong selected id** |
| Proven that production already mixed rows? | **Cannot prove without DB/audit of clone/upload history** |

---

## 8. Recommended verification (ops, not cosmetic)

1. On prod DB: compare distinct employee/sector hashes for `uploads.client_id IN (2,4)`; look for identical filename fingerprints across tenants (clone signature `clone_{destino.id}_…`).  
2. Reproduce: admin session, open Converplast dashboard, rapidly switch to Roda without full reload — watch Network for overlapping `/api/dashboard?client_id=2` completing after `client_id=4`.  
3. Confirm operator role: if reporter is admin, treat as context/race first; if bound user `client_id=2` saw Roda PII, escalate as true authorization failure (not found in current bound-user path).  

---

## File index (key)

| Path | Role |
|------|------|
| `backend/tenant.py` | `resolve_authorized_client` |
| `backend/auth.py` | JWT / `get_current_user*` |
| `backend/authz.py` | `require_tenant_client`, public path set |
| `backend/main.py` | middleware, `validar_*`, all legacy APIs, clone |
| `backend/analytics.py` | client-scoped aggregations |
| `frontend/static/js/auth.js` | `getCurrentClientId`, fetch Bearer inject |
| `frontend/static/js/clientes.js` | selection + chart cache clear |
| `frontend/static/js/dashboard.js` | load race / section toggle |
| `frontend/static/js/comparativos.js` | fallback `client_id=1` |
| `tests/test_s01a_tenant_guard.py` | core tenant unit/API tests |
| `docs/integration/FIT04_RESOURCE_OWNERSHIP.md` | prior export leak note |
