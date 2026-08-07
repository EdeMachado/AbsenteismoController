# FIT-03 — Matriz de Segurança por Endpoint

**Branch:** `integration/foundation-train`  
**Baseline HEAD (FIT-02):** `79fac6a946c3276a13a60be0724d5d6b8c49ec3c`  
**Escopo:** fechamento de autenticação/autorização/tenant nas APIs legadas.  
**Inventário:** introspecção FastAPI (`app.routes`) — não apenas busca textual.

## Política de classes

| Classe | Significado |
|--------|-------------|
| 1. Pública intencional | Sem Bearer; allowlist explícita |
| 2. Autenticada sem tenant | Bearer; sem binding de cliente |
| 3. Autenticada e vinculada ao tenant | Bearer + `validar_acesso_client_id` / `resolve_authorized_client` |
| 4. Exclusiva de administrador | `is_admin=True` explícito |
| 5. Exclusiva de perfil técnico | N/A nesta train (não há modelo separado além de admin) |
| 6. Desativada/removida | Restore HTTP ausente; docs condicionais |

## Gate transversal

| Mecanismo | Papel |
|-----------|-------|
| `api_auth_middleware` | 401 em `/api/*` fora de `PUBLIC_API_PATHS` sem Bearer JWT válido |
| `backend/authz.py` | `require_authenticated_user`, `require_admin`, `require_tenant_client`, `api_docs_enabled` |
| `validar_acesso_client_id` | Alinhado a `resolve_authorized_client`: NULL sem admin → 403 |
| `ENABLE_API_DOCS` / `ENVIRONMENT` | Docs OpenAPI desabilitados por default em production |

## Rotas registradas: 96 handlers HTTP (método×path)

### API (`/api/*`)

| Método | Path | Função | Arquivo | Finalidade | Consumidor FE | Classe | Auth | Tenant | Admin | Perfil | Params tenant | Risco pré-FIT-03 | Correção | Testes | Status |
|--------|------|--------|---------|------------|---------------|--------|------|--------|-------|--------|---------------|------------------|----------|--------|--------|
| GET | `/api/alertas` | `obter_alertas` | `backend/main.py` | Alertas | index.html | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/analises/cids` | `analise_cids` | `backend/main.py` | Análise CIDs | analises | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/analises/funcionarios` | `analise_funcionarios` | `backend/main.py` | Análise funcionários | funcionarios.html, analises | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/analises/setores` | `analise_setores` | `backend/main.py` | Análise setores | analises | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/apresentacao` | `dados_apresentacao` | `backend/main.py` | Dados apresentação | apresentacao.html | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/auth/login` | `login` | `backend/main.py` | Autenticação JWT | login.html | Pública intencional | não | não | não | — | — | N/A | allowlist PUBLIC_API_PATHS; health sanitizado | test_fit03_api_auth_smoke / test_s01a_tenant_guard | PÚBLICO OK |
| POST | `/api/auth/logout` | `logout` | `backend/main.py` | Logout | auth.js | Autenticada sem tenant | sim | não | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/auth/me` | `get_current_user_info` | `backend/main.py` | Perfil sessão | auth.js | Autenticada sem tenant | sim | não | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/backup/create` | `create_backup_manual` | `backend/main.py` | Criar backup | configuracoes / admin | Exclusiva de administrador | sim | N/A / admin | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/backup/list` | `list_backups` | `backend/main.py` | Listar backups | configuracoes / admin | Exclusiva de administrador | sim | N/A / admin | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/buscar-cnpj/{cnpj}` | `buscar_cnpj` | `backend/main.py` | Busca CNPJ | clientes.html | Autenticada sem tenant | sim | não | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/cadastro-empresa` | `cadastro_empresa` | `backend/main.py` | Cadastro empresa (lead) | landing.html (agora admin-only) | Exclusiva de administrador | sim | N/A / admin | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/clientes` | `listar_clientes` | `backend/main.py` | Listar clientes | clientes.html, index.html, auth pages | Autenticada e vinculada ao tenant | sim | sim | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/clientes` | `criar_cliente` | `backend/main.py` | Criar cliente | clientes.html, index.html, auth pages | Exclusiva de administrador | sim | sim (filtro user) | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/clientes/{client_id}/campos-disponiveis` | `obter_campos_disponiveis` | `backend/main.py` | obter campos disponiveis | config graficos | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/clientes/{client_id}/column-mapping` | `get_column_mapping` | `backend/main.py` | get column mapping | upload / config | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| PUT | `/api/clientes/{client_id}/column-mapping` | `save_column_mapping` | `backend/main.py` | save column mapping | upload / config | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/clientes/{client_id}/column-mapping/preview` | `preview_column_mapping` | `backend/main.py` | preview column mapping | páginas autenticadas / auth.js | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/clientes/{client_id}/graficos` | `obter_graficos_configurados` | `backend/main.py` | obter graficos configurados | dashboard/index | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| PUT | `/api/clientes/{client_id}/graficos` | `salvar_graficos_configurados` | `backend/main.py` | salvar graficos configurados | dashboard/index | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/clientes/{client_id}/graficos/gerar-dados` | `gerar_dados_grafico_personalizado` | `backend/main.py` | gerar dados grafico personalizado | páginas autenticadas / auth.js | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| DELETE | `/api/clientes/{cliente_id}` | `deletar_cliente` | `backend/main.py` | Excluir cliente | clientes.html | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/clientes/{cliente_id}` | `obter_cliente` | `backend/main.py` | Detalhe cliente | clientes.html | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| PUT | `/api/clientes/{cliente_id}` | `atualizar_cliente` | `backend/main.py` | Editar cliente | clientes.html | Exclusiva de administrador | sim | sim | sim | is_admin=True | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/clientes/{cliente_id}/arquivar` | `arquivar_cliente` | `backend/main.py` | Arquivar cliente | páginas autenticadas / auth.js | Exclusiva de administrador | sim | sim | sim | is_admin=True | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/clientes/{cliente_id}/ativar` | `ativar_cliente` | `backend/main.py` | Ativar cliente | páginas autenticadas / auth.js | Exclusiva de administrador | sim | sim | sim | is_admin=True | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/clientes/{cliente_id}/clonar_dados` | `clonar_dados_cliente` | `backend/main.py` | Clonar dados entre tenants | clientes.html (admin) | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/clientes/{cliente_id}/cores` | `obter_cores_cliente` | `backend/main.py` | obter cores cliente | clientes.html | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| PUT | `/api/clientes/{cliente_id}/cores` | `salvar_cores_cliente` | `backend/main.py` | salvar cores cliente | clientes.html | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/clientes/{cliente_id}/logo` | `upload_logo_cliente` | `backend/main.py` | upload logo cliente | clientes.html | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/clientes/{cliente_id}/logos` | `listar_logos_cliente` | `backend/main.py` | listar logos cliente | clientes.html | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| DELETE | `/api/clientes/{cliente_id}/logos/{logo_id}` | `deletar_logo_cliente` | `backend/main.py` | deletar logo cliente | páginas autenticadas / auth.js | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| PUT | `/api/clientes/{cliente_id}/logos/{logo_id}/principal` | `definir_logo_principal` | `backend/main.py` | definir logo principal | páginas autenticadas / auth.js | Autenticada e vinculada ao tenant | sim | sim | não | — | path client(e)_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/config` | `get_config` | `backend/main.py` | Ler configs | configuracoes.html | Autenticada sem tenant | sim | não | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/config/{chave}` | `get_config_value_api` | `backend/main.py` | Ler config | páginas autenticadas / auth.js | Autenticada sem tenant | sim | não | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| PUT | `/api/config/{chave}` | `update_config` | `backend/main.py` | Atualizar config | páginas autenticadas / auth.js | Exclusiva de administrador | sim | N/A / admin | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/dados` | `criar_dado` | `backend/main.py` | Criar atestado | páginas autenticadas / auth.js | Autenticada e vinculada ao tenant | sim | sim | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/dados/todos` | `listar_todos_dados` | `backend/main.py` | Listar atestados | dados_powerbi.html | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| DELETE | `/api/dados/{atestado_id}` | `excluir_dado` | `backend/main.py` | Excluir atestado | dados_powerbi.html | Autenticada e vinculada ao tenant | sim | sim | não | — | recurso→client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/dados/{atestado_id}` | `obter_dado` | `backend/main.py` | Detalhe atestado | dados_powerbi.html | Autenticada e vinculada ao tenant | sim | sim | não | — | recurso→client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| PUT | `/api/dados/{atestado_id}` | `atualizar_dado` | `backend/main.py` | Atualizar atestado | dados_powerbi.html | Autenticada e vinculada ao tenant | sim | sim | não | — | recurso→client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/dashboard` | `dashboard` | `backend/main.py` | Dashboard agregado | index.html | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/export/excel` | `export_excel` | `backend/main.py` | Export Excel | relatorios/export | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/export/pptx` | `export_pptx` | `backend/main.py` | Export PPTX | apresentacao/export | Autenticada e vinculada ao tenant | sim | sim | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/filtros` | `obter_filtros` | `backend/main.py` | Filtros dashboard | index/dashboard | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/filtros-salvos` | `listar_filtros_salvos` | `backend/main.py` | listar filtros salvos | dashboard filtros | Autenticada e vinculada ao tenant | sim | sim | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/filtros-salvos` | `salvar_filtro` | `backend/main.py` | salvar filtro | dashboard filtros | Autenticada e vinculada ao tenant | sim | sim | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| DELETE | `/api/filtros-salvos/{filtro_id}` | `deletar_filtro` | `backend/main.py` | deletar filtro | páginas autenticadas / auth.js | Autenticada e vinculada ao tenant | sim | sim | não | — | recurso→client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| PUT | `/api/filtros-salvos/{filtro_id}` | `atualizar_filtro` | `backend/main.py` | atualizar filtro | páginas autenticadas / auth.js | Autenticada e vinculada ao tenant | sim | sim | não | — | recurso→client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/filtros-salvos/{filtro_id}/aplicar` | `aplicar_filtro_salvo` | `backend/main.py` | aplicar filtro salvo | páginas autenticadas / auth.js | Autenticada e vinculada ao tenant | sim | sim | não | — | recurso→client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| PUT | `/api/funcionario/atualizar` | `atualizar_funcionario` | `backend/main.py` | Atualizar funcionário | páginas autenticadas / auth.js | Autenticada e vinculada ao tenant | sim | sim | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/funcionario/perfil` | `perfil_funcionario` | `backend/main.py` | Perfil funcionário | perfil_funcionario.html | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| PUT | `/api/funcionarios/atualizar-massa` | `atualizar_funcionarios_massa` | `backend/main.py` | Update em massa | páginas autenticadas / auth.js | Autenticada e vinculada ao tenant | sim | sim | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/health` | `health_check` | `backend/main.py` | Health sanitizado | ops/monitoring | Pública intencional | não | não | não | — | — | N/A | allowlist PUBLIC_API_PATHS; health sanitizado | test_fit03_api_auth_smoke / test_s01a_tenant_guard | PÚBLICO OK |
| GET | `/api/health/integrity` | `health_check_integrity` | `backend/main.py` | Integridade DB (admin) | admin/ops | Exclusiva de administrador | sim | N/A / admin | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/notifications` | `get_notifications` | `backend/main.py` | Notificações | shell/auth | Exclusiva de administrador | sim | não (usuário) | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| PUT | `/api/notifications/{notification_id}/read` | `mark_notification_read` | `backend/main.py` | Marcar notificação | páginas autenticadas / auth.js | Exclusiva de administrador | sim | não (usuário) | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/preview/{upload_id}` | `preview_data` | `backend/main.py` | Preview upload | preview.html | Autenticada e vinculada ao tenant | sim | sim | não | — | recurso→client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/produtividade` | `obter_produtividade` | `backend/main.py` | Listar produtividade | produtividade.html | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/produtividade` | `salvar_produtividade` | `backend/main.py` | Criar produtividade | produtividade.html | Autenticada e vinculada ao tenant | sim | sim | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/produtividade/evolucao` | `obter_evolucao_produtividade` | `backend/main.py` | Evolução produtividade | produtividade.html | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| DELETE | `/api/produtividade/{produtividade_id}` | `excluir_produtividade` | `backend/main.py` | Excluir produtividade | páginas autenticadas / auth.js | Autenticada e vinculada ao tenant | sim | sim | não | — | recurso→client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| PUT | `/api/produtividade/{produtividade_id}` | `atualizar_produtividade` | `backend/main.py` | Atualizar produtividade | páginas autenticadas / auth.js | Autenticada e vinculada ao tenant | sim | sim | não | — | recurso→client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/relatorios/comparativo` | `comparativo_periodos` | `backend/main.py` | Comparativo períodos | comparativos.html | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/tendencias` | `tendencias` | `backend/main.py` | Tendências | tendencias.html | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/upload` | `upload_file` | `backend/main.py` | Upload legado | upload.html | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/upload/analyze` | `analyze_file` | `backend/main.py` | Analisar planilha | upload_inteligente.html | Autenticada e vinculada ao tenant | sim | sim | não | — | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/upload/process` | `process_file_with_config` | `backend/main.py` | Processar upload | upload_inteligente.html | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/uploads` | `list_uploads` | `backend/main.py` | Listar uploads | upload.html, dados_powerbi | Autenticada e vinculada ao tenant | sim | sim | não | — | query/form client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| DELETE | `/api/uploads/{upload_id}` | `delete_upload` | `backend/main.py` | Excluir upload | páginas autenticadas / auth.js | Autenticada e vinculada ao tenant | sim | sim | não | — | recurso→client_id | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| GET | `/api/users` | `list_users` | `backend/main.py` | Listar usuários | configuracoes.html | Exclusiva de administrador | sim | N/A / admin | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/users` | `create_user` | `backend/main.py` | Criar usuário | configuracoes.html | Exclusiva de administrador | sim | N/A / admin | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/users/atualizar-permissoes` | `atualizar_permissoes_usuarios` | `backend/main.py` | Permissões (admin; script legado desativado) | páginas autenticadas / auth.js | Exclusiva de administrador | sim | N/A / admin | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| DELETE | `/api/users/{user_id}` | `delete_user` | `backend/main.py` | Excluir usuário | páginas autenticadas / auth.js | Exclusiva de administrador | sim | N/A / admin | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| PUT | `/api/users/{user_id}` | `update_user` | `backend/main.py` | Editar usuário | páginas autenticadas / auth.js | Exclusiva de administrador | sim | N/A / admin | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |
| POST | `/api/users/{user_id}/desativar` | `desativar_user` | `backend/main.py` | Desativar usuário | páginas autenticadas / auth.js | Exclusiva de administrador | sim | N/A / admin | sim | is_admin=True | — | aberto anônimo | Depends auth + middleware JWT; tenant/admin conforme classe | test_fit03_api_auth_smoke / test_s01a_tenant_guard | FECHADO |

### Páginas HTML (shell)

| Método | Path | Função | Arquivo | Finalidade | Consumidor FE | Classe | Auth API | Tenant | Admin | Status |
|--------|------|--------|---------|------------|---------------|--------|----------|--------|-------|--------|
| GET | `/` | `index` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/analises` | `analises_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/apresentacao` | `apresentacao_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/apresentacao` | `pagina_apresentacao` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/auto_processor` | `auto_processor_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/clientes` | `pagina_clientes` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/comparativos` | `comparativos_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/configuracoes` | `configuracoes_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/dados_powerbi` | `dados_powerbi_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/dashboard_powerbi` | `dashboard_powerbi_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/funcionarios` | `funcionarios_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/index.html` | `index_html` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/landing` | `landing_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/login` | `login_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/perfil_funcionario` | `perfil_funcionario_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/preview` | `preview_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/produtividade` | `produtividade_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/tendencias` | `tendencias_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/upload` | `upload_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |
| GET | `/upload_inteligente` | `upload_inteligente_page` | `backend/main.py` | Shell HTML | navegador | Pública intencional (shell HTML) | via auth.js nas APIs | N/A página | não | SHELL OK |

### Assets / docs

| Path | Classe | Política | Status |
|------|--------|----------|--------|
| `/static/*` | Pública intencional | assets estáticos | OK |
| `/docs`, `/redoc`, `/openapi.json` | Condicional | `api_docs_enabled()` — off em production por default; on em development/staging/test ou `ENABLE_API_DOCS=1` | POLÍTICA OK |
| Restore backup via HTTP | Desativada | Não há rota de restore registrada | AUSENTE (desejado) |
| Ingestion `/api/ingestion/*` | Flag + auth | Só registra com `ENABLE_INTELLIGENT_INGESTION` + PR4 guard; fail-closed | NÃO REGISTRADA (flags off) |

## Resumo quantitativo

- Handlers HTTP totais: **96**
- API `/api/*`: **76**
- Páginas HTML: **20**
- API públicas intencionais: **2** (`POST /api/auth/login`, `GET /api/health`)
- API autenticadas: **74**
- Rotas `/api/*` sem auth na signature (excl. públicas): **0**

## Regras de tenant (confirmadas)

- Não-admin: tenant = `user.client_id`; request não é fonte de verdade.
- `client_id=NULL` sem `is_admin` → **403** (listagem e acesso).
- Admin: somente com `is_admin=True`; sem fallback `client_id=1`.
- Sem rota HTTP de restore de backup.

## Residual conhecido (não bloqueador de fechamento de auth)

- `landing.html` chama `POST /api/cadastro-empresa` sem token; agora exige admin (intencional). Sem redesign UX neste FIT.
- `download_app.html` referencia `/api/download/app` (rota não registrada — pré-existente).
- Minimização de PII em payloads analíticos permanece dívida de produto (auth/tenant fechados).

