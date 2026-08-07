# EXEC-01 — Baseline Snapshot

| Campo | Valor |
|-------|-------|
| **Documento** | `docs/executive/EXEC01_BASELINE_SNAPSHOT.md` |
| **Marco** | `v2.0-foundation-stable` (annotated tag) |
| **Branch espelho** | `release/v2-foundation-stable` |
| **HEAD exato** | `540cda0806326aa14ced57d42fd43e8a69817d08` |
| **FIT-08** | CONCLUÍDO (Smoke GO; banco preservado) |
| **Clientes produção** | 2 — CONVERPLAST; 4 — RODA DE OURO |
| **Escopo** | Snapshot de retorno antes do redesign executivo experimental |

## 1. Objetivo do marco

Ponto permanente de retorno ao sistema operacional homologado **antes** de qualquer tela EXEC-01.
Este marco **não deve ser alterado** após criação.

## 2. Arquitetura no HEAD

- Auth / tenant (FIT-03)
- MetricService (métricas canônicas)
- DataQualityService / IQB (A02-A)
- Performance Engine (Epic 2A — flag OFF em produção)
- Intelligent Ingestion (flag OFF)
- Security Registry / CORS / Headers / CI
- Dashboard legado (`/`, Power BI pages, análises, comparativos, tendências, produtividade)

## 3. Telas / rotas atuais (legado)

| Rota | Função |
|------|--------|
| `/` | Dashboard operacional |
| `/dados_powerbi` | Meus Dados |
| `/dashboard_powerbi` | Dashboard Power BI |
| `/produtividade` | Produtividade |
| `/upload` | Upload mensal |
| `/apresentacao` | Apresentação |
| `/funcionarios` | Funcionários |
| `/comparativos` | Comparativos |
| `/configuracoes` | Configurações |
| `/analises` | Análises |
| `/tendencias` | Tendências |

## 4. Gráficos existentes

Inventário completo: `docs/executive/EXEC01_EXISTING_CHART_AUDIT.md`.

## 5. APIs analíticas principais

- `/api/dashboard`, `/api/dados`, `/api/analises/*`, `/api/tendencias`, `/api/relatorios/comparativo`, `/api/produtividade*`
- Shadow/métricas canônicas e IQB via serviços internos (não substitutos do dashboard)

## 6. Feature flags (produção / baseline)

| Flag | Estado baseline |
|------|-----------------|
| `ENABLE_INTELLIGENT_INGESTION` | `false` |
| `ENABLE_BIOMED_PERFORMANCE_ENGINE` | `false` |
| `ENABLE_EXECUTIVE_UI` | **não existia** no HEAD; introduzida como `false` em EXEC-01 |

## 7. Banco

- Preservado no deploy FIT-08; sem migration nesta iniciativa.
- Snapshot de retorno de código: tag acima. Backup DB operacional permanece sob rotina FIT-08 (fora deste repositório de código).

## 8. Rollback

1. Checkout / deploy do commit `540cda0806326aa14ced57d42fd43e8a69817d08` (tag `v2.0-foundation-stable`).
2. Garantir `ENABLE_EXECUTIVE_UI=false` (e demais flags experimentais OFF).
3. Não é necessário migration de rollback para EXEC-01 (sem alteração de schema).

## 9. Política

- Não alterar este documento para refletir o novo visual até homologação formal.
- Desenvolvimento EXEC-01 ocorre em `feat/executive-intelligence-redesign`.
