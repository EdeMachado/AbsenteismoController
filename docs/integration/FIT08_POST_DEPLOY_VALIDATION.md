# FIT-08 — Post-Deploy Validation

## Identificação do smoke

| Campo | Valor |
|-------|-------|
| Script | `scripts/fit08_block6_smoke_production.sh` |
| Revisão | **FIT08-B6-R3** |
| Resultado | **SMOKE_RESULT=GO** |
| FAIL_COUNT | **0** |
| HEAD produção | `540cda0806326aa14ced57d42fd43e8a69817d08` |

## Serviço e health

| Check | Resultado |
|-------|-----------|
| `systemctl is-active` | **active** |
| GET `/api/health` | HTTP **200** |
| `status` | **ok** |
| `database.healthy` | **true** |
| integrity (API) | **true** |
| Porta `127.0.0.1:8000` | escutando |

## Páginas reais (FastAPI)

| Função | Rota | Resultado |
|--------|------|-----------|
| home/dashboard | `/` | 200 (contrato real) |
| login | `/login` | 200 |
| clientes | `/clientes` | 200 |
| funcionários | `/funcionarios` | 200 |
| upload | `/upload` | 200 |
| produtividade | `/produtividade` | 200 |
| dados Power BI | `/dados_powerbi` | 200 |
| dashboard Power BI | `/dashboard_powerbi` | 200 |
| NAO_REGISTRADA | `/dashboard`, `/dados-powerbi` | não usadas como gate |

## Autenticação / APIs

| Check | Resultado |
|-------|-----------|
| Health público | 200 |
| Login probe inválido | **401** (rota pública acessível) |
| APIs protegidas sem token | **401** (nunca 200/500) |
| Docs `/docs` `/redoc` `/openapi.json` | **404** / OFF |
| Experimentais | não acessíveis anonimamente; UI experimental 404 |

## Segurança de borda

| Check | Resultado |
|-------|-----------|
| CSP / XFO / XCTO / Referrer / Permissions | aprovados |
| Cache-Control APIs sensíveis | no-store / private |
| HSTS (HTTPS oficial) | aprovado |
| CORS origem oficial | refletida |
| CORS origem aleatória | sem Allow-Origin |

## Inventário agregado (readonly)

Eventos por cliente via:

```sql
SELECT COUNT(*) FROM atestados a
INNER JOIN uploads u ON a.upload_id = u.id
WHERE u.client_id = ?
```

| Métrica | Esperado | Observado |
|---------|----------|-----------|
| Cliente 2 presente | 1 | 1 |
| Cliente 2 uploads | 18 | 18 |
| Cliente 2 eventos | 4520 | 4520 |
| Cliente 4 presente | 1 | 1 |
| Cliente 4 uploads | 14 | 14 |
| Cliente 4 eventos | 333 | 333 |
| Users total | 3 | 3 |
| Admins ativos | 2 | 2 |
| Non-admin sem tenant | 0 | 0 |
| Senhas comuns | 0 | 0 |

## Banco

| Check | Resultado |
|-------|-----------|
| `PRAGMA quick_check` | **ok** |
| `PRAGMA integrity_check` | **ok** |
| SHA antes/depois smoke | **idêntico** |
| Escrita pelo smoke | **não** |

## Flags

| Flag | Estado |
|------|--------|
| Ingestão inteligente | OFF |
| Performance engine | OFF |
| API docs | OFF |

## Conclusão pós-deploy

Produção **saudável** após deploy controlado FIT-08.  
Sem migration, sem restore, sem rollback.
