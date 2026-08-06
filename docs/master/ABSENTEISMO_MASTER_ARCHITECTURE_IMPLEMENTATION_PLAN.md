# Absenteísmo Controller — Master Architecture & Implementation Plan

**Documento vivo de governança e execução.**  
**Repositório:** https://github.com/EdeMachado/AbsenteismoController  
**Produção:** https://www.absenteismocontroller.com.br  
**Baseline `origin/main` (consolidação documental):** `d0c012abaae9191531c3d2f30cb909407d31af01`  
**Data de consolidação:** 2026-08-06

---

## 1. Princípio absoluto

Nenhuma melhoria poderá colocar em risco: banco, dados, uploads, históricos, usuários, senhas, permissões, acessos, autenticação, clientes ou a operação da funcionária.

**Proibido sem autorização explícita + backup + rollback:** migration, seed destrutivo, cópia de banco local→VPS, reset de senha no startup, dedupe histórico silencioso, reprocessamento em massa, merge/deploy automático.

---

## 2. Estado atual (baseline)

### Produção

| Item | Valor |
|------|--------|
| Host | Hostinger VPS |
| App | `/var/www/absenteismo` |
| DB | `/var/www/absenteismo/database/absenteismo.db` |
| Stack | Nginx + Gunicorn/UvicornWorker + FastAPI + SQLAlchemy + SQLite + HTML/JS/CSS |
| Serviço | `absenteismocontroller.service` |
| Clientes | CONVERPLAST `client_id=2`; RODA DE OURO `client_id=4` |
| Responsividade | Corrigida e publicada (PR #3) |

**Backup validado (referência):**  
`/root/backups/absenteismo/absenteismo_pre_responsividade_20260806_180357.db`  
`quick_check: ok` · `integrity_check: ok`  
SHA-256: `d45a309f79546e62fafc4a515da895a0a998c6e0ff6eb7314a9d72db19395315`

### PRs em andamento (confirmados nesta consolidação)

| PR | Branch | HEAD | Base | Draft | Mergeable | Escopo |
|----|--------|------|------|-------|-----------|--------|
| [#4](https://github.com/EdeMachado/AbsenteismoController/pull/4) | `fix/s01a-auth-tenant-guard` | `0d1a2a6` | `main` | **draft** | MERGEABLE/CLEAN | Auth/tenant/startup seguro |
| [#5](https://github.com/EdeMachado/AbsenteismoController/pull/5) | `feat/a01a-canonical-metrics-shadow` | `ce0bb99` | `main` | **draft** | MERGEABLE/CLEAN | Métricas canônicas shadow |
| [#6](https://github.com/EdeMachado/AbsenteismoController/pull/6) | `feat/a02a-data-quality-shadow` | `9cd0414` | `feat/a01a-…` | **Ready for review** | MERGEABLE/CLEAN | IQB / qualidade shadow |

---

## 3. Arquitetura-alvo (visão)

```text
PLANILHA BRUTA
    → ARQUIVO ORIGINAL PRESERVADO (RAW)
    → CONVERSOR INTELIGENTE
    → VALIDAÇÃO E PRÉVIA + IQB DO ARQUIVO
    → HASH / PREVENÇÃO DE REUPLOAD
    → IMPORTAÇÃO IDEMPOTENTE
    → CAMADA CANÔNICA (métricas)
    → BIOMED INTELLIGENCE ENGINE
    → MÉTRICAS OFICIAIS + DASHBOARDS
    → MOTOR DE REGRAS → BIOMED INSIGHT
    → PLANO DE AÇÃO → MONITORAMENTO
```

Camadas de dados: **RAW → STANDARDIZED → CURATED** (detalhe em `ABSENTEISMO_TARGET_ARCHITECTURE.md` e `ABSENTEISMO_DATA_GOVERNANCE.md`).

---

## 4. Quatro épicos (não executar em um único PR)

| Épico | Nome | Foco |
|-------|------|------|
| **E1** | Fundação analítica e entrada de dados | Consolidar #5/#6 + conversor + preview + hash + idempotência |
| **E2** | Biomed Intelligence Engine + Dashboard 2.0 | Motor central; gráficos oficiais; substituição gradual |
| **E3** | Biomed Insight | Regras determinísticas + payload seguro + plano de ação + IA narrativa |
| **E4** | Consolidação corporativa | Segurança, LGPD, backup, CI, deploy, logs, modularização |

Regras: branch própria, testes, docs, PR draft, **parada antes de merge**, sem deploy automático. Não iniciar o próximo épico antes da entrega técnica do anterior.

Detalhes: `ABSENTEISMO_EPIC_{1,2,3,4}_PLAN.md`.

---

## 5. Conflitos entre PRs

| Par | Sobreposição de arquivos | Risco |
|-----|--------------------------|-------|
| #4 × #5 | Quase nula (#5 só `backend/services/*`, tests, docs analytics) | **Baixo** |
| #4 × #6 | Nula no diff direto (#6 empilhado em #5) | **Baixo** |
| #5 × #6 | #6 **depende** de #5 (base da branch) | **Dependência estrutural** |
| #4 × main | Altera `backend/main.py`, `auth`, frontend | Isolado dos analytics |

**Conclusão:** não há conflito de conteúdo relevante entre segurança (#4) e analytics (#5/#6). O único acoplamento forte é o **empilhamento #6 → #5**.

---

## 6. Ordem exata de merge (proposta)

> Merge **somente** com autorização explícita + backup + smoke plan. Esta seção **não autoriza** merge.

1. **PR #5** → `main` (fundação canônica; independente; draft até aprovação).  
2. **Retarget PR #6** para `main` (após #5 mergeado) → merge #6.  
3. **PR #4** → `main` (segurança/tenant) — pode ser antecipado para **antes** de #5 se a prioridade operacional for auth; tecnicamente é ortogonal.  
   - **Ordem preferencial de risco de produto:** `#4` (proteger produção) → `#5` → `#6`.  
   - **Ordem preferencial de stack analítica:** `#5` → `#6`, com `#4` em paralelo ou intercalado.

**Recomendação consolidada (produto + risco):**

1. Merge **#4** (auth/tenant) — reduz exposição enquanto analytics ainda é shadow.  
2. Merge **#5** (métricas canônicas).  
3. Retarget + merge **#6** (IQB).  
4. Só então abrir PRs do Épico 1 (conversor/hash/idempotência) em cima de `main` atualizado.

---

## 7. Ordem exata de implementação (código novo)

1. Consolidação documental *(esta entrega)*.  
2. Aprovação/merge governado de #4, #5, #6 *(humano)*.  
3. **Épico 1** — conversor, preview, hash, reupload, idempotência, docs.  
4. **Épico 2** — intelligence engine + dashboard gradual.  
5. **Épico 3** — regras + insight + plano de ação.  
6. **Épico 4** — segurança plena, LGPD, backup Linux, CI, deploy, logs, modularização.

---

## 8. Critérios de aceite globais

- Zero escrita acidental em produção.  
- Tenant explícito; sem `client_id=1` fallback.  
- Sem PII em saídas analíticas/IA.  
- Testes do escopo verdes.  
- PR draft → revisão → Ready → autorização → backup → merge → deploy → smoke → rollback pronto.  
- Shadow antes de substituir dashboard.

---

## 9. Riscos principais

| Risco | Mitigação |
|-------|-----------|
| Merge de #6 sem #5 | Manter stack; retarget só após #5 |
| Deploy sem backup | Gate obrigatório (`ABSENTEISMO_DEPLOY_GOVERNANCE.md`) |
| Reupload acumulando KPI | Hash + política no Épico 1; sem dedupe silencioso histórico |
| Taxa oficial sem denominador | Só publicar com horas previstas confiáveis |
| Big-bang no `main.py` | Extração incremental de services/routers |
| IA com PII | Payload agregado + guardrails Épico 3 |

---

## 10. Documentos deste pacote

| Arquivo | Conteúdo |
|---------|----------|
| `ABSENTEISMO_MASTER_ARCHITECTURE_IMPLEMENTATION_PLAN.md` | Este documento |
| `ABSENTEISMO_TARGET_ARCHITECTURE.md` | Arquitetura-alvo |
| `ABSENTEISMO_EPIC_1_PLAN.md` … `_4_` | Planos por épico |
| `ABSENTEISMO_DATA_GOVERNANCE.md` | RAW/STD/CURATED + identidade |
| `ABSENTEISMO_DEPLOY_GOVERNANCE.md` | Pipeline e gates |
| `ABSENTEISMO_ROLLBACK_STRATEGY.md` | Rollback |
| `ABSENTEISMO_SECURITY_MODEL.md` | Auth/tenant/perfis |
| `ABSENTEISMO_ANALYTICS_MODEL.md` | Métricas e shadow |
| `ABSENTEISMO_AI_GOVERNANCE.md` | Insight / proibições IA |

---

## 11. O que **não** foi feito nesta consolidação

- Nenhum código funcional novo (conversor, dashboard, IA, migration).  
- Nenhum merge.  
- Nenhum deploy.  
- Nenhum acesso de escrita ao VPS/banco.  
- PR #6 marcado **Ready for review** apenas (sem merge).
