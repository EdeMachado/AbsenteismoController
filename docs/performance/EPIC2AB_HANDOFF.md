# Epic 2A-B — Handoff

## Escopo entregue

Adaptador canônico + IQB + resolução/comparabilidade de janelas + `PerformanceShadowService` + CLI readonly, em cima do motor metodologicamente aprovado (HEAD prévio `a096e28`).

## Pacote

| Módulo | Papel |
|--------|-------|
| `canonical_snapshot_adapter.py` | MetricService → MetricSnapshot |
| `data_quality_adapter.py` | DataQualityService → QualityBundle |
| `window_resolver.py` | janelas nominadas + comparabilidade |
| `readonly_guard.py` | path/produção/integridade/schema/ro |
| `performance_shadow_service.py` | orquestração shadow |
| `scripts/shadow_performance_engine.py` | CLI |

## Flag

`ENABLE_BIOMED_PERFORMANCE_ENGINE=false` (default). Sem HTTP/UI.

## Limitações conhecidas

1. Fonte mensal ≠ precisão diária.
2. Produtividade BioMed não lida do banco legado.
3. `recorrencia` / `afastamentos_longos` ausentes no contrato canônico → `None` + limitação.
4. Headcount só via `--efetivo-trabalhadores` (não inventado).
5. Associação temporal ≠ causalidade.
6. Esta etapa **não** executa contra backup real nem VPS.

## Próximo passo controlado

Uma única validação sobre cópia readonly já auditada (tenants 2 e 4), ainda sem merge/deploy/produção.
