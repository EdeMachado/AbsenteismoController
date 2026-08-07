# FIT-06 — Plano de Deploy (não executar nesta etapa)

## Identidade

- **DR:** FIT06-DR1  
- **PR:** #11 · Ready for review · base `main`  
- **HEAD gate auditado:** `fcd81f4215dfcd8c24512ea993b74c87ac624fd2`  
- **App:** `/var/www/absenteismo` · `127.0.0.1:8000` · `absenteismocontroller.service`  
- **Clientes:** `2` CONVERPLAST · `4` RODA DE OURO  

## Pré-condições (todas obrigatórias)

1. CI Foundation verde  
2. Backup atualizado validado (`FIT06_BACKUP_PROTOCOL.md`)  
3. Inventário agregado coerente (admins > 0, tenants 2/4 presentes)  
4. Env production pronto (seção Config)  
5. Autorização humana explícita para merge **e** deploy  
6. `DEPLOY_DE_CODIGO_SEM_MIGRATION=true`  

## Método de merge recomendado: **merge commit**

Justificativa: o PR integra histórico de vários PRs (#4–#10 + FIT train). Merge commit preserva rastreabilidade do train; squash perderia a narrativa de segurança/fundação; rebase reescreveria SHAs já referenciados nos docs FIT.

**Não executar merge neste FIT.**

### Sequência de merge (humano)

1. Congelar HEAD do PR (anotar SHA)  
2. Confirmar CI verde  
3. Confirmar backup atualizado  
4. Confirmar inventário  
5. Confirmar configurações  
6. Autorizar merge humano  
7. Merge commit PR #11 → `main`  
8. Capturar novo SHA de `main`  
9. Não fechar PRs antigos antes da validação pós-deploy  
10. Não apagar branch `integration/foundation-train`  

## Configuração exigida no deploy

| Variável | Valor esperado | Verificação |
|----------|----------------|-------------|
| `ENVIRONMENT` | `production` | presente + normalizado |
| `ENABLE_INTELLIGENT_INGESTION` | `false` | presente + false |
| `ENABLE_BIOMED_PERFORMANCE_ENGINE` | `false` | presente + false |
| `ENABLE_API_DOCS` | `false` / `0` / ausente | docs off |
| `CORS_ALLOWED_ORIGINS` | domínio oficial (sem `*`) | presente |
| `SECRET_KEY` | **existente, não substituir** | PRESENT only |
| DB path | `/var/www/absenteismo/database/absenteismo.db` | sem override experimental |
| `INGESTION_ALLOW_TEST_DEPENDENCIES` | `false` / ausente | |
| `INGESTION_SQLITE_PATH` | ausente | |

Nunca imprimir o valor de `SECRET_KEY`.

## Estratégia de deploy (futuro)

1. Registrar HEAD atual da produção (`git rev-parse HEAD` em `/var/www/absenteismo`)  
2. Registrar novo HEAD de `main`  
3. Confirmar backup FIT-06  
4. Confirmar working tree  
5. **Preservar untracked:** `database/`, `logs/`, `gunicorn_config.py`, `nohup.out`  
6. Atualizar somente arquivos versionados (`git fetch` + `git checkout`/`git pull` do SHA mergeado — **sem** `git clean`, **sem** reset que apague untracked necessários)  
7. Instalar dependências se necessário (`venv` + `pip install -r requirements.txt`) — não upgrade amplo  
8. Manter flags OFF  
9. Validar import: `venv/bin/python -c "import backend.main"`  
10. Reiniciar serviço **uma** vez: `systemctl restart absenteismocontroller.service`  
11–20. Smoke: status, health, login, dashboard, clientes, Converplast, Roda de Ouro, logs, banco; rollback imediato se falhar  

## Proteção de untracked

| Artefato | Ação |
|----------|------|
| `database/` | Nunca sobrescrever; backup prévio obrigatório |
| `gunicorn_config.py` | Copiar para `/root/backups/absenteismo/config_<ts>/` antes do pull |
| `logs/` | Preservar |
| `nohup.out` | Preservar |

**Proibido:** `git clean -fdx`, `git reset --hard` seguido de limpeza que remova untracked necessários.

## Impacto no banco

Declaração:

```
DEPLOY_DE_CODIGO_SEM_MIGRATION=true
```

Evidência no código do PR:

- Ingestão OFF → SQL Epic1 **não** aplicado  
- Performance Engine OFF → sem schema novo  
- `run_migrations()` apenas `ensure_column(clients.logo_url)` — no-op se coluna já existe (produção atual)  
- `init_db()`/`create_all` não altera tabelas existentes  
- Startup **não** altera usuários/clientes/senhas/tenants (S01-A)

## Impacto no login / tokens

| Tópico | Comportamento |
|--------|---------------|
| `SECRET_KEY` | **Não trocar** no deploy |
| Tokens pré-deploy | Continuam válidos até `exp` se a chave for a mesma |
| Expiração | 480 minutos (8h) — `ACCESS_TOKEN_EXPIRE_MINUTES` |
| Restart | Não invalida JWT (stateless) |
| Frontend 401 | `auth.js` limpa storage e redireciona `/login` |
| Logout forçado | Não necessário se SECRET_KEY preservada |

## Dependências

Comparar `requirements.txt` no venv (gunicorn, FastAPI 0.115.0, SQLAlchemy 2.0.36, python-jose, python-multipart, openpyxl, pandas, fpdf2, python-pptx). Instalar faltantes **antes** do restart. Não atualizar versões amplamente nesta janela.

## Smoke pós-deploy

### Imediato
systemctl active · health ok · database healthy · login admin · login tenant · dashboard · clientes 2/4 · flags experimentais off/404 · sem 500 nos logs · tenant cruzado 403  

### 15 min / 60 min
memória · locks SQLite · erros recorrentes · exportação · produtividade  

### Próximo uso operacional
Validação com a funcionária no fluxo real (sem dados novos de teste em produção)  
