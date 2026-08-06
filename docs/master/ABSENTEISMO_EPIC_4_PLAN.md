# Épico 4 — Consolidação corporativa

## Objetivo

Endurecer segurança, LGPD, backup, deploy, CI, observabilidade e modularização — em **PRs separados por risco**.

## Pré-requisitos

- PR #4 (S01-A) mergeado como base de auth/tenant.  
- Preferível após estabilização analítica mínima (#5/#6).

## Escopos (PRs separados)

1. **Segurança** — APIs, IDOR, perfis, rate limit, sessão, CORS, CSP, secrets.  
2. **LGPD** — minimização, logs, retenção, pseudonimização, RIAs.  
3. **Backup Linux** — cron, checksum, checks, cópia externa, restore testado.  
4. **CI** — compile, unit, tenant, auth, lint, deps.  
5. **Deploy** — pipeline repetível + health + smoke + rollback.  
6. **Observabilidade** — logging estruturado, correlation ID, mascaramento.  
7. **Banco** — Alembic + plano PostgreSQL **somente se critérios** (§40) forem atingidos.  
8. **Modularização** — routers/services/repositories incrementais.

## Critérios de aceite

- Nenhum endpoint crítico sem auth/tenant.  
- Backup restaurável com evidência.  
- Deploy com gate de backup.  
- Testes §46.  
- Sem “PR monólito”.

## Backlog (resumo)

Ver seções 38–47 do master plan; cada bullet vira ticket com PR próprio quando priorizado.
