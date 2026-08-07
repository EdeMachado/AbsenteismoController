# FIT-04 — Release Candidate FIT04-RC1

## Identidade

| Campo | Valor |
|-------|-------|
| RC | **FIT04-RC1** (identificador documental; sem tag remota) |
| Branch | `integration/foundation-train` |
| HEAD inicial (obrigatório) | `88cf672f394cf2c68ff120d7d74a0d916fc89f6c` |
| HEAD FIT-04 | `1e4ec6321539b4c101bac72e04ab0c9d4bf6d979` |
| PR | https://github.com/EdeMachado/AbsenteismoController/pull/11 (draft) |
| Ambiente staging | `/tmp/abs-fit04-rc-20260806-231537` · porta **18081** |
| Config hash (requirements+authz+cors) | `15116b470622a28e2c946029d296449c0631d7af8b53917c28d69016e6b4efc1` |
| Python | 3.12.3 |
| FastAPI | 0.115.0 |
| SQLAlchemy | 2.0.36 |

## Flags (obrigatoriamente OFF)

```
ENABLE_INTELLIGENT_INGESTION=false
ENABLE_BIOMED_PERFORMANCE_ENGINE=false
```

## Escopo validado

1. Gate JWT + frontend (auth.js order, Bearer, 401/403)  
2. Landing institucional (Alt. A) — sem cadastro anônimo  
3. Ownership por recurso + exports/filtros  
4. CORS/headers/cache  
5. Inventário runtime 100% classificado  
6. Startup não destrutivo (3 ciclos seed; SHA DB estável em health-only)  
7. Cálculos sintéticos estáveis pós-middleware  
8. Browser Playwright multi-viewport/perfis — PASS  
9. CI mínimo GitHub Actions  
10. Suíte: **455 passed**

## Limitação JWT documentada

Sem revogação server-side de token; logout remove storage local. Sessões multi-aba compartilham `localStorage`. Aceitável nesta fase.

## Proibido / confirmado

- Produção / VPS / banco vivo **não acessados**  
- Sem migration / merge / deploy  
- Sem alteração de usuários/clientes reais  
