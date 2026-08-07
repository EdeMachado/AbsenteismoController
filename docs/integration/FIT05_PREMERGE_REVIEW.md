# FIT-05 — Pre-Merge Review Package

## Decisão

**Ready for review: GO**  
**Merge em `main`: NO-GO** (exige autorização humana + backup validado)  
**Deploy: NO-GO** nesta etapa

---

## Identidade do RC

| Campo | Valor |
|-------|-------|
| RC | FIT04-RC1 |
| Branch | `integration/foundation-train` |
| HEAD FIT-04 (gate) | `8f66cd55debf3eade8ea488c1cf606ee3f3ae8ce` |
| Base | `main` |
| PR | https://github.com/EdeMachado/AbsenteismoController/pull/11 |
| Mergeabilidade (conferida) | `MERGEABLE` / `CLEAN` |

## Testes (execução final local FIT-05)

| Suite | Resultado |
|-------|-----------|
| Completa (`pytest tests/`) | **455 passed** |
| Inventário de rotas | 0 não classificadas; 76 `/api/*` |
| Tenant / resource ownership | OK |
| Startup não destrutivo | OK |
| Landing | OK (Alt. A; sem cadastro anônimo) |
| CORS / headers | OK |
| Exports | OK (tenant assert) |
| Frontend estático (auth.js) | OK |
| Métricas / IQB / ingestão / Performance / privacidade | OK (flags OFF) |

## Cobertura

Pacotes fundação (auth, authz, tenant, cors, registry, metrics, data_quality, ingestion, performance): **87.12%** (≥87% gate).

## Segurança

- Gate JWT em `/api/*` (FIT-03/04)
- Zero rota crítica anônima
- Docs OpenAPI off em production por default
- Health sanitizado
- Restore HTTP ausente
- CI sem secrets / sem deploy

## Tenant

- `client_id=NULL` sem admin → 403
- Ownership por recurso (upload, produtividade, dados, cliente)
- Exports e filtros-salvos com `resolve_authorized_client`
- Sem fallback `client_id=1`

## Rotas públicas

Somente:

- `POST /api/auth/login`
- `GET /api/health`

## Flags (confirmadas OFF)

```
ENABLE_INTELLIGENT_INGESTION=false
ENABLE_BIOMED_PERFORMANCE_ENGINE=false
```

`ENABLE_API_DOCS`: desligado por default quando `ENVIRONMENT=production`.  
Startup **não** ativa feature flags.

## Banco / migrations

- Staging FIT-04/05: SQLite sintético descartável apenas
- Produção / VPS / banco vivo: **não acessados**
- `run_migrations()` no startup apenas garante coluna legada `clients.logo_url` (pré-existente; não é migration experimental Epic1)
- Sem migration Epic1 / Performance no startup
- Sem seed destrutivo; sem admin padrão; sem alteração de tenant/senha

## CI

Workflow: `.github/workflows/foundation-ci.yml`

Contém: install deps · py_compile/import · conflict markers · bloqueio `.db`/`.sqlite`/`.env`/backup · inventário/segurança · suíte completa · coverage ≥87% · **sem deploy**.

## Arquivos proibidos no PR

Confirmado ausentes como adições do PR:

- `.db` / `.sqlite` / `.sqlite3` / backup / dump / `.env` secret
- Nomes Converplast / Roda de Ouro em paths adicionados
- Fixtures usam tenants sintéticos Alpha/Beta; campos CPF/matrícula apenas sintéticos para testes anti-PII (não são dados reais)

Working tree local pode ter artefatos não rastreados (`.coverage`, `backups/`, docs de auditoria) — **fora do PR**.

## Compatibilidade de produção (revisão estática)

| Item | Status |
|------|--------|
| `requirements.txt` | FastAPI 0.115.0, SQLAlchemy 2.0.36, gunicorn, JWT, multipart, openpyxl/fpdf2/pptx |
| CORS | Sem wildcard em production; `CORS_ALLOWED_ORIGINS` no deploy |
| Flags | Default OFF |
| DB path | Override só via `ABSENTEISMO_SQLITE_PATH`; recusa path vivo `/var/www/...` |
| Schema legado | Sem alteração estrutural nova obrigatória para merge |

## Riscos residuais (explícitos)

1. **JWT sem revogação server-side** — logout é localStorage; tokens válidos até expirar.  
2. **Módulos novos continuam OFF** — ingestão inteligente e Performance Engine não entram em produção pelo merge.  
3. **Ingestão** requer banco/schema experimental futuro se/quando a flag for ligada.  
4. **Performance Engine** permanece shadow.  
5. **CORS de produção** depende de configurar `CORS_ALLOWED_ORIGINS` corretamente no deploy.  
6. **SQLite em produção** exige **backup validado** antes de atualizar a aplicação.  
7. Cobertura fundação expandida ~87% (FIT-02 citava ~89% em superfície menor).  
8. Minimização de PII em payloads analíticos legados permanece dívida de produto.

## Checklist de merge (humano)

- [ ] Review de código aprovado por humano  
- [ ] CI verde no PR  
- [ ] Backup do SQLite de produção validado (restore testado)  
- [ ] Confirmar flags OFF no ambiente alvo  
- [ ] Confirmar `CORS_ALLOWED_ORIGINS` / `ENVIRONMENT=production`  
- [ ] Janela de manutenção definida  
- [ ] Autorização explícita para merge  

## Checklist de deploy futuro (não executar agora)

- [ ] Backup prévio + checksum  
- [ ] Deploy artefato da revisão mergeada  
- [ ] Smoke health + login  
- [ ] Verificar um tenant sintético/staging espelho se existir  
- [ ] Rollback plan pronto  
- [ ] **Não** ligar `ENABLE_INTELLIGENT_INGESTION` / `ENABLE_BIOMED_PERFORMANCE_ENGINE` sem épico dedicado  

## Rollback

- Manter artefato/commit anterior de `main`  
- Restaurar backup SQLite se houver alteração de dados (este PR não deve exigir migration destrutiva)  
- Reinício do serviço na revisão anterior  

## Estado do PR nesta etapa

- Atualizar body com pacote FIT-05  
- Marcar **Ready for review**  
- **Não** mergear  
- **Não** deployar  
