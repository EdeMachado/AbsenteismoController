# FIT-06 — GO / NO-GO (Deployment Readiness)

## Decisão atual: **GO PARA MERGE HUMANO** (atualizado por FIT-07)

> Status operacional completo e evidências finais:  
> [`FIT07_FINAL_MERGE_GATE.md`](./FIT07_FINAL_MERGE_GATE.md)  
> **Deploy:** ainda **NÃO AUTORIZADO**.

## Motivo da reavaliação (FIT-07)

Bloqueadores do NO-GO anterior foram sanados com evidência objetiva:

1. **Foundation CI SUCCESS** no HEAD `85de239b3b741e9801903251aec509f11cf54e51`  
   - run: [31134794005](https://github.com/EdeMachado/AbsenteismoController/actions/runs/31134794005)  
   - check `foundation`: SUCCESS  
2. **Backup pré-merge** criado e validado no VPS (execução humana):  
   - `/root/backups/absenteismo/absenteismo_pre_fit06_20260807_000226.db`  
   - SHA-256 `13c485ace101695b792ac1dd9f634cd9291ccc381b33dbaeb79f3f316acae1ff`  
   - quick_check / integrity_check / backup_*: **ok**  
3. **Inventário** coerente (clientes 2 e 4; volumes agregados; 2 admins ativos; 0 orphan non-admin).  
4. **Segurança:** conta operacional (Nilceia) — somente hash de senha atualizado; tenant/perms preservados; senhas comuns = 0 (sem registrar segredos).  
5. **Config:** `ENVIRONMENT=production`; `SECRET_KEY` presente; flags OFF; API docs OFF; `DEPLOY_DE_CODIGO_SEM_MIGRATION=true`.

## O que está GO

| Item | Status |
|------|--------|
| PR Ready for review | OK |
| Base `main` | OK |
| Mergeable + CI verde (evidência FIT-07) | OK |
| Backup pré-merge validado | OK |
| Inventário agregado | OK |
| Segurança pós-correção de senha comum | OK |
| Flags OFF / env production | OK |
| `DEPLOY_DE_CODIGO_SEM_MIGRATION=true` | OK |
| Plano merge/deploy/rollback/backup | OK (docs FIT-06) |
| Script diagnóstico/backup | OK (`scripts/fit06_prod_diag_backup.sh`) |

## Condições (checklist)

- [x] CI Foundation **verde** no HEAD de evidência do PR  
- [x] Backup `absenteismo_pre_fit06_<ts>.db` criado e validado (SHA + integrity)  
- [x] Inventário agregado coerente (admins ativos ≥1; clientes 2 e 4 presentes)  
- [x] Env production: flags OFF, SECRET_KEY presente (sem print)  
- [x] Autorização documental FIT-07 para merge humano  
- [ ] Merge humano explícito na UI (pendente)  
- [ ] Deploy (bloqueado)

## NO-GO absoluto se (ainda válidos para abortar)

- backup/integrity falhar  
- nenhum admin ativo  
- SECRET_KEY ausente  
- migration experimental necessária  
- CI vermelho no tip a mergear  
- working tree perigosa / risco de `git clean`  
- banco vivo não confirmado  

## Deploy

**NO-GO** — deploy **não autorizado** mesmo após merge.  
Deploy só em etapa futura, com autorização humana explícita + plano FIT-06.

## Confirmações

- Sem merge automático neste pacote  
- Sem deploy  
- Sem acesso/alteração automática à produção ou banco vivo  
