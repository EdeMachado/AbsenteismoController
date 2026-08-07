# FIT-08 — Production Deploy Report

## Decisão

**Deploy de código CONCLUÍDO** em produção.  
**Migration:** não executada.  
**Rollback:** não executado (disponível).

## Identidade

| Campo | Valor |
|-------|-------|
| App | `/var/www/absenteismo` |
| Serviço | `absenteismocontroller.service` |
| Porta | `127.0.0.1:8000` |
| OLD_HEAD | `d0c012abaae9191531c3d2f30cb909407d31af01` |
| DEPLOYED_HEAD / TARGET | `540cda0806326aa14ced57d42fd43e8a69817d08` |
| PR de fundação | [#11](https://github.com/EdeMachado/AbsenteismoController/pull/11) (merged) |
| Modo | `DEPLOY_DE_CODIGO_SEM_MIGRATION=true` |

## Backups

| Artefato | Path / valor |
|----------|----------------|
| Banco pré-deploy | `/root/backups/absenteismo/absenteismo_pre_fit06_20260807_000226.db` |
| SHA-256 | `13c485ace101695b792ac1dd9f634cd9291ccc381b33dbaeb79f3f316acae1ff` |
| Config pré-FIT-08 | `/root/backups/absenteismo/config_pre_fit08_20260807_005949` |
| Conteúdo config | `.env` + `gunicorn_config.py` preservados |

## Sequência executada (humana)

1. Bloco 1 pré-deploy RO → `PREDEPLOY_RESULT=GO`
2. Bloco 2 prepare config → `CONFIG_RESULT=GO` (`SECRET_KEY` preservada)
3. Bloco 3 FF code → `CODE_UPDATE_RESULT=GO` · `DEPLOYED_HEAD=540cda0…`
4. Bloco 4+5 deps + import + **restart único** → `BLOCK45_RESULT=GO`
5. Bloco 6 smoke **FIT08-B6-R3** → `SMOKE_RESULT=GO` · `FAIL_COUNT=0`

## Preservações

| Item | Status |
|------|--------|
| Banco vivo | preservado (SHA antes/depois idêntico no smoke) |
| Usuários / tenants | preservados |
| `SECRET_KEY` | inalterada |
| Flags experimentais | OFF |
| API docs | OFF |
| Untracked críticos | preservados |

## Não ocorrido

- migration / SQL Epic 1 / tabelas `ingestion_*` novas  
- ativação de flags  
- restore automático de banco  
- rollback  
- segundo restart  

## Resultado

```
OLD_HEAD=d0c012abaae9191531c3d2f30cb909407d31af01
TARGET_HEAD=540cda0806326aa14ced57d42fd43e8a69817d08
DEPLOYED_HEAD=540cda0806326aa14ced57d42fd43e8a69817d08
SERVICE_STATUS=active
SMOKE_RESULT=GO
DEPLOY_RESULT=SUCCESS
```
