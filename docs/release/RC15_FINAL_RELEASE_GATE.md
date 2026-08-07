# RC-1.5 — Final Release Gate

**Branch:** `cursor/rc15-final-release-gate-f8f5`  
**Status:** Draft · **NÃO MERGEAR** · **NÃO DEPLOYAR** · sem restart · sem migration  
**Verdict:** `GO` (merge only this cumulative tip; see §4)

---

## 1. Baseline

| Item | Value |
|------|-------|
| Repo | `EdeMachado/AbsenteismoController` |
| Produção / main estável | `540cda0806326aa14ced57d42fd43e8a69817d08` |
| PR final de produto (RC-1.4) | #24 @ `c4604a856ed25862848d8ab4951328c9fa39690a` |
| Tip com gate (este PR) | branch `cursor/rc15-final-release-gate-f8f5` @ `c4604a856ed25862848d8ab4951328c9fa39690a` (sobre #24) |

Prova main ⊆ tip: `git merge-base --is-ancestor 540cda08 <FINAL_HEAD>` = true;  
`git rev-list --count <FINAL_HEAD>..540cda08` = 0.

---

## 2. HEAD final

O tip auditável para release é o **HEAD deste PR RC-1.5** (gate fail-closed + registry + testes), não o tip nu do #24.

O #24 sozinho **não** bloqueava `/preview/*`, `/staging/*`, `/api/preview/ficha*`, `/f/*` em `ENVIRONMENT=production` e falhava Foundation CI no inventário de rotas (`/api/preview/ficha/*` fora de `KNOWN_API_PATHS`).

---

## 3. Cadeia de ancestry (PRs #13–#24)

Método: `gh pr view <n> --json headRefOid` +  
`git merge-base --is-ancestor <tip> 18bf397` +  
`git rev-list --count 18bf397..<tip>`.

| PR | Tip OID (prefix) | Ancestor of #24? | Commits ahead of #24 | Classificação |
|----|------------------|------------------|----------------------|---------------|
| #13 | `adffcd16…` | YES | 0 | Código funcional (EXEC-01→03); SUPERSEDED |
| #14 | `bc81e98b…` | YES | 0 | Código funcional (EXEC-08); SUPERSEDED |
| #15 | `6b583dd5…` | YES | 0 | Código funcional (EXEC-09); SUPERSEDED |
| #16 | `72f55612…` | YES | 0 | Código funcional (EXEC-10); SUPERSEDED |
| #17 | `2b92d9e7…` | YES | 0 | Código + preview identidade; SUPERSEDED |
| #18 | `458ad3a3…` | YES | 0 | Preview audit; SUPERSEDED |
| #19 | `4b7da8cf…` | YES | 0 | Preview excellence; SUPERSEDED |
| #20 | `5c448810…` | YES | 0 | RC-1.1 consolidação; SUPERSEDED |
| #21 | `d2749fd0…` | YES | 0 | RC-1.2 funcional; SUPERSEDED |
| #22 | `b1ad697a…` | YES | 0 | RC-1.2A landing + ficha in-memory; SUPERSEDED |
| #23 | `2e887d5c…` | YES | 0 | RC-1.3 linguagem; SUPERSEDED |
| #24 | `18bf3974…` | YES (self) | 0 | RC-1.4 presentation; SUPERSEDED após RC-1.5 |

**Conclusão:** cadeia cumulativa / stacked. Nenhum commit necessário das PRs #13–#23 está fora do tip #24.  
Documentação/preview e código funcional convivem na mesma stack; não há tip paralelo com código obrigatório.

---

## 4. Estratégia de merge recomendada

**A — Mergear SOMENTE o PR deste RC-1.5** (tip que contém #24 + gate fail-closed).

Não mergear #13–#24 individualmente. Não mergear #24 nu.

Após o merge do tip RC-1.5 em `main`, encerrar como **SUPERSEDED**:

`#13, #14, #15, #16, #17, #18, #19, #20, #21, #22, #23, #24`

**Não executar merge nesta etapa.**

---

## 5. PRs superseded

Após merge do RC-1.5 tip: **#13–#24** (todos ancestrais integrais / tip produto subsumido).

---

## 6. Flags (fail-closed)

| Flag | Default produção | Notas |
|------|------------------|-------|
| `ENABLE_EXECUTIVE_UI` | `false` | UI/API executiva |
| `ENABLE_EXECUTIVE_PRESENTATION` | `false` | requer UI pai |
| `ENABLE_INTELLIGENT_INGESTION` | `false` | |
| `ENABLE_BIOMED_PERFORMANCE_ENGINE` | `false` | |
| `ENABLE_API_DOCS` | `false` | docs só em dev/staging/test se não forçado |
| `ENABLE_PREVIEW_SURFACES` | **OFF em production/prod** | nova (RC-1.5); ON implícito em development/dev/staging/test/local |

Com `ENVIRONMENT=production` e sem overrides: todas OFF. Verificado via import.

---

## 7. Segurança

| Controle | Status |
|----------|--------|
| Auth JWT em `/api/*` não públicos | OK (FIT-03) |
| Tenant isolation | OK (S01-A / FIT) |
| CORS sem wildcard em produção | OK |
| CSP / X-Frame-Options DENY / nosniff | OK |
| HSTS em produção | OK |
| Cache-Control no-store em APIs sensíveis | OK |
| Preview APIs públicas só com gate ON | OK (fail-closed prod) |
| Reset demo `/api/preview/ficha/reset` | PREVIEW_ONLY · 404 em prod |
| `/f/{token}` | PREVIEW_ONLY · token opaco · 404 em prod |
| Docs/debug | OFF por default em prod |
| Segredos versionados | nenhum `.env`/sqlite live adicionado neste gate |
| PII em URL da ficha | proibido por design (token opaco) |

Grep de CPF/matrícula/CID/password/secret/token/clinical/answers: usos legítimos de domínio legado + store preview; sem vazamento de valores neste relatório.

---

## 8. Rotas (contrato)

### PRODUÇÃO LEGADA (flags OFF)

HTML: `/`, `/login`, `/upload`, **`/preview`** (upload preview legado), `/analises`, `/tendencias`, `/apresentacao`, `/funcionarios`, `/clientes`, `/landing`, etc.  
API: `/api/health`, `/api/auth/*`, dashboard, uploads, clientes, export, etc.  
`/api/preview/{upload_id}` permanece **autenticado** (não é homologação).

### PRODUÇÃO NOVA (atrás de flag)

Executive UI/API/presentation — só com `ENABLE_EXECUTIVE_*`.  
Ingestion / performance engines — flags próprias.

### PREVIEW / HOMOLOGAÇÃO (bloqueadas em production)

- `/preview/*` (exceto exatamente `/preview`)
- `/staging/*`
- `/api/preview/ficha/*` (incl. reset)
- `/f/{token}`

Middleware: `backend/preview_gate.py` + `preview_surfaces_middleware`.

### Classificação de artefatos

| Item | Class |
|------|--------|
| `/preview.html` route `/preview` | PRODUCTION_READY (legado) |
| `/preview/landing`, identity, RC previews, presentation-rc | PREVIEW_ONLY |
| `/api/preview/ficha/*`, in-memory store | PREVIEW_ONLY |
| `/f/{token}`, reset demo | PREVIEW_ONLY |
| `scripts/exec02_staging_server.sh`, synth SQLite local | DEV_ONLY / PREVIEW_ONLY |
| Executive modules | SAFE_BEHIND_FLAG |
| Ficha digital in-memory | **PREVIEW_ONLY** (nunca PRODUCTION_READY até persistência) |

---

## 9. Banco

- Nenhuma migration **obrigatória** nova para este release (models inalterados vs main estável na stack RC).
- SQLite atual permanece compatível.
- Nenhuma tabela demo introduzida no schema de produção.
- Startup: `init_db` + `run_migrations` existentes + seeds **não destrutivos** (configs default se ausentes; sem criar admin/senha; sem reescrever tenant).
- Ficha digital: **sem** persistência SQL.

---

## 10. Testes

Local (espelho Foundation CI env):

```
pytest -q tests/  →  548 passed
```

Inclui foundation/FIT auth·CORS·inventory·tenant, executive EXEC-01→11B, release RC-1.1→1.5, compile/import `backend.main`.

Correções de gate:

- Registry: paths `/api/preview/ficha/*` em `KNOWN_API_PATHS` (corrige falha CI do #24).
- Testes EXEC-11/11B alinhados ao copy PT (RC-1.3).
- `tests/release/test_rc15_final_release_gate.py` — bloqueio prod + legado `/preview` liberado.

CI GitHub do #24 (pré-gate): **FAILURE** (route inventory).  
CI deste PR: validar após push (esperado verde com registry + gate).

---

## 11. Riscos

1. Mergear #24 sem RC-1.5 reabre preview/ficha em produção e reintroduz falha de inventário.  
2. Ficha digital permanece in-memory — risco de falsa expectativa de produção.  
3. `ENABLE_PREVIEW_SURFACES=true` em produção reabre homologação (decisão explícita necessária).  
4. Artefatos de screenshot em `tests/artifacts/**` aumentam o peso do repo (não bloqueiam segurança se preview gated).

---

## 12. Rollback readiness

- Main estável `540cda08` permanece ancestral; rollback = redeploy desse SHA.  
- Flags OFF preservam superfície legada.  
- Gate é fail-closed: ausência da flag em prod não expõe preview.  
- Sem migration de schema neste release → rollback sem downgrade SQL.

**ROLLBACK_READY=yes**

---

## 13. GO / NO_GO

| Critério | |
|----------|--|
| Ancestry compreendida | YES |
| Estratégia de merge inequívoca | YES (somente tip RC-1.5) |
| Testes locais verdes | YES (548) |
| Migration necessária | NO |
| Produção com flags OFF preservada | YES |
| Preview/staging bloqueados em production | YES |
| Demo/sintético não exposto em prod | YES |
| Ficha in-memory ≠ production | YES (PREVIEW_ONLY) |
| Segurança sem regressão material | YES |
| Segredos versionados | NONE encontrados neste gate |
| Rollback possível | YES |

**RC15_RESULT=GO** — sob a condição explícita de mergear **este** tip (não #24 isolado), sem deploy automático nesta etapa.

---

## Confirmação operacional

NÃO MERGEAR · NÃO DEPLOYAR · NÃO RESTART · NÃO MIGRATION · NÃO READY-FOR-REVIEW forçado.
