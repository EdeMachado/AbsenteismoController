# EXEC-01 — Entrega

## Status

Experiência experimental **funcional** atrás de `ENABLE_EXECUTIVE_UI=false` (default).
**Sem deploy, sem migration, sem ativação em produção.**

## Entregáveis

1. Snapshot: tag `v2.0-foundation-stable` → `540cda0806326aa14ced57d42fd43e8a69817d08`
2. Branch estável: `release/v2-foundation-stable`
3. Baseline: `docs/executive/EXEC01_BASELINE_SNAPSHOT.md`
4. Branch de desenvolvimento: `feat/executive-intelligence-redesign`
5. Inventário: `docs/executive/EXEC01_EXISTING_CHART_AUDIT.md`
6–9. Decisões de gráficos no inventário (MANTER / MELHORAR / CONSOLIDAR / SUBSTITUIR / REMOVER)
10. Design System: CSS + `BIOMED_EXECUTIVE_DESIGN_SYSTEM.md`
11. Command Center: `/executive` + módulos de navegação
12. KPIs calculáveis via MetricService / IQB (sem inventar denominador)
13. Novas análises: Pareto CID (grupo alfabético), setores, qualidade, comparabilidade, ROI bloqueado
14. Performance BioMed (estrutura produção/cobertura/execução/resultado)
15. Condicionantes (schema + UI)
16. Narrativa técnica (rule engine, linguagem BioMed)
17. Arquitetura IA: rule engine + schemas + fallback determinístico (sem LLM)
18. Plano de Ação (proposta → validação médica → …)
19. ROI: somente `ROI_NAO_CALCULAVEL` até premissas válidas
20. Privacidade: sem ranking nominal; threshold n<5; assert_no_pii
21. Feature flag `ENABLE_EXECUTIVE_UI`
22. Rotas: `/executive`, `/api/executive/*`
23. APIs agregadas (command-center, intelligence, action-plan, performance, meta)
24. Testes: `tests/executive/test_exec01_executive_ui.py`
25. Artefatos de viewport: `tests/artifacts/executive_screenshots/`
26. Score via `PerformanceService.executive_score` (sem fórmula paralela; sem 50 neutro)

## Limitações

- Série temporal mensal canônica ainda não populada no payload (legado mantém evolução)
- Performance de produção/cobertura depende de registro explícito (não inventado)
- ROI não calculável sem custos/horas compatíveis
- Sem LLM real
- Ficha clínica apenas reservada na navegação

## Próximos passos

- Homologar visual com dados de staging
- Ligar série temporal canônica
- Binding de ações/condicionantes persistidos
- Visual QA com screenshots reais (Playwright) em CI
- Gate humano antes de qualquer flag ON / merge deploy

## Parar

Antes de merge em produção / deploy / migration / ativação de flags.
