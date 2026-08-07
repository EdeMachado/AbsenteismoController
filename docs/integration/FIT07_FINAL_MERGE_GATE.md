# FIT-07 — Final Merge Gate

## Decisão documental

| Gate | Decisão |
|------|---------|
| **Merge humano** | **GO PARA MERGE HUMANO** |
| **Deploy** | **NÃO AUTORIZADO** |

Este documento registra evidências finais para o PR #11.  
Não autoriza deploy, restart, migration, acesso VPS automático nem merge automático.

## Identidade

| Campo | Valor |
|-------|-------|
| PR | https://github.com/EdeMachado/AbsenteismoController/pull/11 |
| Branch | `integration/foundation-train` → `main` |
| HEAD de evidência CI (pré-docs FIT-07) | `85de239b3b741e9801903251aec509f11cf54e51` |
| DR / RC | FIT06-DR1 / FIT04-RC1 |
| Método de merge recomendado | **merge commit** |
| `DEPLOY_DE_CODIGO_SEM_MIGRATION` | `true` |

## 1. Foundation CI

| Item | Evidência |
|------|-----------|
| Conclusão | **SUCCESS** |
| HEAD | `85de239b3b741e9801903251aec509f11cf54e51` |
| Workflow run | [31134794005](https://github.com/EdeMachado/AbsenteismoController/actions/runs/31134794005) |
| Check `foundation` | **SUCCESS** |
| Evento | `pull_request` |

Jobs do run 31134794005: Checkout, compat `/workspace`, SQLite descartável, import, guards, suite de segurança, suite completa e coverage gate — todos **success**.

> Se este arquivo for commitado após `85de239…`, o tip do PR muda; o merge humano deve exigir Foundation CI **SUCCESS** também no HEAD tip documentado no PR.

## 2. Backup pré-merge (evidência humana VPS)

| Item | Valor |
|------|-------|
| Arquivo | `/root/backups/absenteismo/absenteismo_pre_fit06_20260807_000226.db` |
| SHA-256 | `13c485ace101695b792ac1dd9f634cd9291ccc381b33dbaeb79f3f316acae1ff` |
| quick_check | ok |
| integrity_check | ok |
| backup_quick_check | ok |
| backup_integrity_check | ok |

Nenhum conteúdo do banco, PII ou segredo é reproduzido aqui.

## 3. Inventário (agregados)

| Item | Valor |
|------|-------|
| Clientes 2 e 4 | confirmados |
| Converplast (client_id=2) | 18 uploads · 4.520 eventos |
| Roda de Ouro (client_id=4) | 14 uploads · 333 eventos |
| Administradores ativos | 2 |
| Usuário tenant Converplast | 1 |
| Não-administradores sem tenant | 0 |
| Roda de Ouro | acessível pelos administradores |

Sem listagem de usernames, e-mails, hashes ou PII.

## 4. Segurança (resumo)

- Conta operacional referida como Nilceia: **somente** atualização do hash da senha (sem mudança de tenant/permissões).
- Tenant e permissões preservados.
- Contas com senha comum após correção: **0**.
- Este documento **não** registra senha, username, hash ou segredo.

## 5. Configuração (produção — evidência humana)

| Item | Valor |
|------|-------|
| `ENVIRONMENT` | `production` |
| `SECRET_KEY` | presente e preservada (valor não registrado) |
| Ingestão inteligente | OFF por padrão |
| Performance Engine | OFF por padrão |
| API docs | OFF por padrão em produção |
| Deploy de código sem migration | `true` |

## 6. Escopo do que este gate autoriza

**Autorizado (humano):** merge do PR #11 em `main` via merge commit, após revisão.

**Não autorizado:**

- deploy de código
- restart de serviço
- acesso/alteração automática à VPS
- migration experimental
- ligar feature flags
- `git clean` destrutivo
- merge automático por bot

## 7. Checklist final

- [x] Foundation CI SUCCESS no HEAD de evidência `85de239…` (run 31134794005)
- [x] Backup pré-merge validado (SHA + integrity)
- [x] Inventário agregado coerente
- [x] Segurança: senhas comuns = 0; tenant/perms preservados
- [x] Env production / flags OFF / SECRET_KEY presente
- [x] `DEPLOY_DE_CODIGO_SEM_MIGRATION=true`
- [ ] Merge humano explícito (pendente — fora do escopo deste agente)
- [ ] Deploy (bloqueado — etapa futura)

## Confirmações deste pacote documental

- Sem merge automático  
- Sem deploy  
- Sem restart  
- Sem alteração de código funcional neste gate  
