# FIT-04 — Browser Validation

**RC:** FIT04-RC1  
**Branch:** `integration/foundation-train`  
**Baseline HEAD:** `88cf672f394cf2c68ff120d7d74a0d916fc89f6c`  
**Ambiente:** `/tmp/abs-fit04-rc-20260806-231537` · porta `18081` · SQLite sintético  
**Driver:** Playwright Chromium  
**Resultado:** **PASS** (`failed_count=0`)

## Resoluções

390×844 · 768×1024 · 1024×768 · 1366×768

## Páginas

`/login`, `/landing`, `/`, `/clientes`, `/dados_powerbi`, `/funcionarios`, `/upload`, `/produtividade`

## Perfis

| Perfil | Credencial sintética | Resultado |
|--------|----------------------|-----------|
| Admin | `fit04_admin` | OK — páginas + auth.js |
| Tenant A | `fit04_user_a` (client_id=2) | OK |
| Tenant B | `fit04_user_b` (client_id=4) | OK |
| Sem token | — | protected → `/login` |
| Landing | — | sem chamada a cadastro API |

## auth.js / token

- Páginas autenticadas carregam `auth.js` (verificado no DOM).
- Token injetado via API login + `localStorage`.
- Sem token: redireciona para login.
- Com token: não bounce indevido nas páginas de negócio.
- Visitante autenticado em `/login` é redirecionado para `/clientes` (comportamento legado esperado).

## Como reproduzir (local gate)

```bash
python3 scripts/fit04_setup_staging.py
# subir uvicorn :18081 com ABSENTEISMO_SQLITE_PATH impresso
FIT04_BASE_URL=http://127.0.0.1:18081 FIT04_DB=... python3 scripts/fit04_browser_validation.py
pytest -q tests/test_fit04_browser_static.py
```

CI executa a parte estática/HTTP; navegador permanece gate local documentado.
