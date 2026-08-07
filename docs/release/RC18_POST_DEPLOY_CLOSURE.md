# RC-1.8 — Post-Deploy Closure & Release Baseline

**Status:** Deploy closure formalizado · **FLAGS OFF** · **sem novo deploy/restart**  
**Date (UTC):** 2026-08-07

---

## Resumo executivo

O Release Candidate (stack RC-1.5 / merge PR #25 + docs RC-1.6) foi implantado em produção via procedimento RC-1.7 (Blocks 1–6 = GO).

Produção permanece funcionalmente equivalente à superfície legada: **todas as experiências novas OFF**, preview/homologação bloqueados, Ficha Digital **PREVIEW_ONLY**.

**RC18_RESULT=GO**

---

## 1. Baseline de produção

| Campo | Valor |
|-------|-------|
| PREVIOUS_PRODUCTION_HEAD | `540cda0806326aa14ced57d42fd43e8a69817d08` |
| CURRENT_PRODUCTION_HEAD | `fefa1996d37004c88dfb2087166544ea05be9e8f` |
| MAIN_RELEASE_MERGE (PR #25) | `9ed88591f08a5261abb09d7d9e03493a52dff2c3` |
| SERVICE | `absenteismocontroller.service` = **active** |
| HEALTH_HTTP | **200** |

Delta `9ed8859..fefa199` = somente documentação RC-1.6 (já validado no plano RC-1.7).

---

## 2. Banco (pós-deploy)

| Campo | Valor |
|-------|-------|
| DB_SIZE_BYTES | `3547136` |
| DB_SHA256 | `bfabfb0364846d2ab55a1b0f7119f5090e892a327638e53b355b461cc488d1b4` |
| PRAGMA_QUICK_CHECK | `ok` |
| PRAGMA_INTEGRITY_CHECK | `ok` |
| DB_PRESERVED | **yes** (deploy de código sem migration) |

Inventário agregado (sem PII):

| Métrica | Valor |
|---------|-------|
| client_ids | `[2, 4]` |
| users | `3` |
| atestados | `4853` |
| uploads | `32` |
| common_plaintextish_passwords | `0` |

---

## 3. Backup oficial pré-deploy

| Campo | Valor |
|-------|-------|
| Path | `/root/backups/absenteismo/rc17_predeploy_20260807_154809` |
| Conteúdo esperado | DB (`sqlite3.Connection.backup`) + `.env` + `gunicorn_config.py` + MANIFEST/SHA |
| Política | **Não mover · não deletar · não sobrescrever** |

Hashes / metadados: permanecer nos arquivos `.sha256` / `MANIFEST.txt` do diretório acima (valores sensíveis de `.env` não são reimpressos neste documento).

`BACKUP_CONFIRMED=yes`

---

## 4. Smoke final (RC-1.7 Block 6)

| Check | Result |
|-------|--------|
| legacy pages | PASS |
| protected APIs (anon → 401) | PASS |
| preview gate (`/preview/*` homolog) | PASS |
| digital form blocked (`/api/preview/ficha/*`, `/f/*`) | PASS |
| API docs blocked | PASS |
| CORS | PASS |
| security headers | PASS |
| DB inventory | PASS |
| flags OFF / legacy posture | PASS |

`SMOKE_RESULT=PASS`  
`SECURITY_RESULT=PASS`

---

## 5. Flags (fail-closed)

Configuração efetiva / postura:

| Flag | Valor efetivo | Nota |
|------|---------------|------|
| `ENABLE_EXECUTIVE_UI` | `false` | OFF explícito ou default fail-closed |
| `ENABLE_EXECUTIVE_PRESENTATION` | `false` | idem |
| `ENABLE_INTELLIGENT_INGESTION` | `false` | idem |
| `ENABLE_BIOMED_PERFORMANCE_ENGINE` | `false` | idem |
| `ENABLE_API_DOCS` | `false` | idem |
| `ENABLE_PREVIEW_SURFACES` | `false` | OFF em `ENVIRONMENT=production` |

Variáveis **ausentes** no `.env` que caem no default `false` / production-off são classificadas como **FAIL-CLOSED** (aceitável).

`FLAGS_OFF=yes`

---

## 6. Ficha Digital

```
DIGITAL_FORM_STATUS=PREVIEW_ONLY
```

**Motivo:** store in-memory (`backend/digital_form/`); sem persistência adequada.  
**Decisão:** não liberar em produção; não criar migration nesta sprint.

---

## 7. Rollback

| Campo | Valor |
|-------|-------|
| ROLLBACK_HEAD | `540cda0806326aa14ced57d42fd43e8a69817d08` |
| ROLLBACK_SCRIPT | `scripts/rc17_block7_rollback.sh` |
| ROLLBACK_SCRIPT_READY | yes |
| DB restore automático | **NO** |
| Backup DB disponível | **YES** (`rc17_predeploy_20260807_154809`) |

Preferir rollback de código preservando o banco. Restore de DB somente com autorização humana explícita.

---

## 8. PR #26 (plan/scripts RC-1.7)

Auditoria:

- Estado: OPEN · draft
- Diff vs `main`: **somente** `docs/release/RC17_PRODUCTION_DEPLOY_PLAN.md` + `scripts/rc17_block1…7_*.sh`
- Nenhuma alteração funcional de produto / schema / flags

### Recomendação: **A — mergear em `main`**

Justificativa: material operacional já usado no deploy bem-sucedido; versionar no tip de `main` preserva rastreabilidade de backup/smoke/rollback para operações futuras. Conteúdo docs+scripts only → merge seguro.

Não executar merge automático nesta etapa RC-1.8 (encerramento documental). Merge humano de #26 quando conveniente.

`PR26_RECOMMENDATION=A_merge_docs_and_scripts_to_main`

---

## 9. Release tag (recomendação — NÃO criar ainda)

Convenção existente no repositório: `v2.0-foundation-stable`.

| Campo | Valor |
|-------|-------|
| RELEASE_TAG_RECOMMENDATION | `v2.1-rc1-production` |
| RELEASE_TAG_TARGET | `fefa1996d37004c88dfb2087166544ea05be9e8f` |
| Criar agora? | **NÃO** |

---

## 10. Próxima etapa (preparar, NÃO executar)

**RC-1.9 — Controlled Feature Activation**

Ativação futura **incremental** (nunca todas as flags de uma vez):

1. `ENABLE_EXECUTIVE_UI`
2. `ENABLE_EXECUTIVE_PRESENTATION`
3. Demais engines (`INGESTION`, `PERFORMANCE`) apenas quando necessárias

**Ficha Digital permanece fora** da sequência até existir persistência adequada.

---

## Decisão

| Item | Valor |
|------|-------|
| RC18_RESULT | **GO** |
| PRODUCTION_HEAD | `fefa1996…` |
| DB_PRESERVED | yes |
| BACKUP_CONFIRMED | yes |
| SMOKE_RESULT | PASS |
| SECURITY_RESULT | PASS |
| FLAGS_OFF | yes |
| DIGITAL_FORM_STATUS | PREVIEW_ONLY |
| ROLLBACK_READY | yes |

### Confirmações operacionais desta etapa

- NÃO ativar flags  
- NÃO restartar  
- NÃO deployar  
- NÃO alterar `.env` / banco  
- NÃO criar tag ainda  
