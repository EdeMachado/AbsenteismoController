# ABSENTEISMOCONTROLLER — FUNCTIONAL INVENTORY

## Legenda de situação

- **OK** — operacional com dados reais (com ressalvas)
- **PARCIAL** — existe UI/API incompleta ou inconsistente
- **QUEBRADO** — rota/arquivo/API ausente ou desconectada
- **STUB** — página “em desenvolvimento”
- **SCHEMA** — modelo existe, sem API/UI efetiva
- **MOCK** — dados simulados

---

## Matriz de funcionalidades

| ID | Módulo | Funcionalidade | Rota(s) | Arquivos | Fonte | Situação | Dados | Segurança | Prioridade |
|----|--------|----------------|---------|----------|-------|----------|-------|-----------|------------|
| F01 | Auth | Login JWT | `/login`, `POST /api/auth/login` | `login.html`, `auth.py` | User DB | OK | Real | Token em localStorage | P0 |
| F02 | Auth | Sessão / me | `/api/auth/me` | `auth.js` | API | **QUEBRADO localmente** se `auth.js` ausente | Real | — | P0 |
| F03 | Usuários | CRUD usuários | `/configuracoes`, `/api/users*` | `configuracoes.*` | User | OK (admin) | Real | Admin | P1 |
| F04 | Clientes | CRUD empresas | `/clientes`, `/api/clientes*` | `clientes.*` | Client | PARCIAL — várias mutações **sem auth** | Real | **Crítico** | P0 |
| F05 | Upload | Planilha mensal | `/upload`, `POST /api/upload` | `upload.*`, `excel_processor.py` | Atestado | OK fluxo; upload **sem auth** | Real | **Crítico** | P0 |
| F06 | Upload inteligente | Analyze/process | `/upload_inteligente` | `upload_inteligente.*` | API | PARCIAL | Real | Sem auth em analyze/process | P1 |
| F07 | Auto processor | Processamento auto | `/auto_processor` | `auto_processor.*` | API | PARCIAL; fora do menu | Real | — | P2 |
| F08 | Dashboard | KPIs + gráficos | `/`, `/api/dashboard` | `index.html`, `dashboard.js`, `analytics.py` | Atestado | OK (auth) | Real | Auth + client check | P1 |
| F09 | Insights | Análises automáticas | via dashboard | `insights.py` | Atestado | OK | Real | — | P2 |
| F10 | Filtros | Período/setor/func | dashboard | `dashboard.js`, `/api/filtros` | DB | PARCIAL — `/api/filtros` sem auth | Real | Médio | P1 |
| F11 | Filtros salvos | CRUD | `/api/filtros-salvos*` | dashboard | SavedFilter | OK (auth) | Real | Auth | P2 |
| F12 | Alertas | Badge + lista | `/api/alertas` | `menu.js`, `alerts.py` | Regras | OK parcial | Real | Auth | P2 |
| F13 | Apresentação | Slides executivos | `/apresentacao` | `apresentacao.*` | Analytics | OK | Real | Auth | P1 |
| F14 | Funcionários | Ranking/lista | `/funcionarios` | `funcionarios.*` | Atestado | OK | Real | — | P1 |
| F15 | Perfil funcionário | Detalhe | `/perfil_funcionario` | `perfil_funcionario.*` | API **sem auth** | PARCIAL | Real/Sensível | **Alto** | P0 |
| F16 | Comparativos | Relatórios | `/comparativos` | `comparativos.*` | API | PARCIAL | Real | — | P1 |
| F17 | Dados tabulares | Editor PowerBI-like | `/dados_powerbi` | `dados_powerbi.*` | `/api/dados*` **sem auth** | PARCIAL | Real/Sensível | **Crítico** | P0 |
| F18 | Dashboard PowerBI | UI alternativa | `/dashboard_powerbi` | `dashboard_powerbi.*` | Misto; trecho “simulado” | PARCIAL/MOCK | Misto | — | P2 |
| F19 | Produtividade | Consultas manuais | `/produtividade` | `produtividade.*` | Tabela produtividade **sem auth API** | PARCIAL | Real (manual) | Alto | P1 |
| F20 | INSS | Colaboradores INSS | UI `inss.html` | `inss.js`, model `ColaboradorINSS` | **Sem rotas backend** | **QUEBRADO** | — | — | P1 |
| F21 | Config | Temas/SMTP/users | `/configuracoes` | `configuracoes.*` | Config/User | OK parcial; GET config público | Real | Médio | P1 |
| F22 | Backup | List/create | `/api/backup*` | `backup_service.py` | Arquivos | PARCIAL — **list sem auth** | — | **Alto** | P0 |
| F23 | Cadastro empresa | Self-service | `/api/cadastro-empresa` | `main.py` | Client/User | PARCIAL sem auth | Real | Médio | P2 |
| F24 | Export | Excel/PPTX | `/api/export/*` | `report_generator.py` | Analytics | OK auth; falta validar acesso client | Real | Médio | P1 |
| F25 | CNPJ | Busca externa | `/api/buscar-cnpj/{cnpj}` | `main.py` | HTTP externo | OK | Externo | Sem auth | P3 |
| F26 | Análises | Página | `/analises` | `analises.html` | — | **STUB** | — | — | P3 |
| F27 | Tendências | Página | `/tendencias` | `tendencias.html` | API sem auth | **STUB**/parcial | — | — | P3 |
| F28 | Preview | Preview upload | `/preview` | `preview.html` | API sem auth | **STUB**/legado | — | — | P3 |
| F29 | Download app | Desktop | `download_app.html` | Electron | — | **Sem rota** FastAPI; link `/dashboard` quebrado | — | — | P2 |
| F30 | Ícone | Utility | `baixar_icone.html` | — | — | Utility; sem rota | — | — | P3 |
| F31 | Relatórios agendados | E-mail | scheduler | `report_scheduler.py` | SMTP | PARCIAL (depende .env) | Real | — | P2 |
| F32 | Notificações | Inbox admin | `/api/notifications*` | `notification_service.py` | DB/serviço | PARCIAL | — | Admin | P2 |
| F33 | IA | — | — | Docs `criação IA.docx` | — | **Não implementada** como módulo | — | — | P3 |
| F34 | Prontuário / ficha clínica | — | — | — | — | **Não existe** como módulo médico formal | — | — | — |
| F35 | CAT / ergonomia / riscos psicossociais | — | — | Slides apresentação (ações saúde) | Conteúdo estático | Conteúdo de apresentação, não CRUD | — | — | P3 |

---

## Funcionalidades de saúde ocupacional vs expectativa

| Esperado em SSO típico | No AbsenteismoController |
|------------------------|--------------------------|
| Prontuário eletrônico | Não |
| Ficha clínica / anamnese | Não |
| Gestão de exames ocupacionais | Não (só contadores manuais em Produtividade) |
| CAT | Não |
| Atestados | Sim (via planilha) |
| CID / diagnóstico | Sim (campos em Atestado) |
| INSS | Modelo + UI; **API ausente** |
| Indicadores absenteísmo | Sim (dashboard) |
| Isolamento multiempresa | Parcial (falhas de auth) |

---

## Mocks / simulados encontrados

| Arquivo | Descrição |
|---------|-----------|
| `dashboard_powerbi.js` (~373) | Comentário/análise “simulado” por tipo de atestado |
| `test_pdf_relatorio_simulado.py` | Teste com gráficos simulados (não produção) |
| Startup `admin`/`admin123` | Credencial padrão seed |
