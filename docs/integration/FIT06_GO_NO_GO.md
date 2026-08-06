# FIT-06 — GO / NO-GO (Deployment Readiness)

## Decisão atual: **NO-GO PARA MERGE HUMANO**

## Motivo principal

1. **CI vermelho** — correções aplicadas no workflow:
   - falso positivo de conflict markers (`=======` vs banners);
   - path SQLite do CI (`ABSENTEISMO_SQLITE_PATH` descartável + `mkdir database`).
   **Aguardar CI verde** no tip.  
2. **Backup atualizado do banco vivo ainda não executado** no VPS (pendência manual obrigatória).  
3. Inventário/admins/CORS de produção ainda não confirmados no servidor.

## O que já está GO (preparação)

| Item | Status |
|------|--------|
| PR Ready for review | OK |
| Base `main` | OK |
| Mergeable (estrutura) | OK (fica UNSTABLE enquanto CI falha) |
| 455 testes locais (FIT-05) | OK |
| Cobertura ≥87% | OK |
| Segurança/tenant/flags OFF | OK |
| `DEPLOY_DE_CODIGO_SEM_MIGRATION=true` | OK |
| Plano merge/deploy/rollback/backup | OK (docs FIT-06) |
| Script diagnóstico/backup | OK (`scripts/fit06_prod_diag_backup.sh`) |

## Condições para reavaliar → GO PARA MERGE HUMANO

Todas obrigatórias:

- [ ] CI Foundation **verde** no HEAD do PR  
- [ ] Backup `absenteismo_pre_fit06_<ts>.db` criado e validado (SHA + integrity)  
- [ ] Inventário agregado coerente (admins ativos ≥1; clientes 2 e 4 presentes)  
- [ ] Env production: flags OFF, CORS configurado, SECRET_KEY presente (sem print)  
- [ ] Dependências do venv compatíveis com `requirements.txt`  
- [ ] Autorização humana explícita  
- [ ] Rollback e preservação de untracked entendidos  

## NO-GO absoluto se

- backup/integrity falhar  
- nenhum admin ativo  
- SECRET_KEY ausente  
- migration experimental necessária  
- CI vermelho  
- working tree perigosa / risco de `git clean`  
- banco vivo não confirmado  

## Deploy

**NO-GO** nesta etapa (e só após merge autorizado + backup).

## Confirmações

- Sem merge  
- Sem deploy  
- Sem acesso/alteração automática à produção ou banco vivo  
