# Absenteísmo Controller — Analytics Model

## Camada canônica (PR #5)

- `MetricService(db).compute(client_id=…, periodo_…)`  
- Métricas shadow; não substituem dashboard ainda.  
- Identidade aproximada; horas registradas ≠ estimadas.  
- Guard anti-PII estruturado.  
- Shadow compare local (fixtures ou `--db-path` readonly explícito).

## Qualidade / IQB (PR #6)

- `DataQualityService` + IQB 0–100.  
- Pesos originais/efetivos; dimensões N/A.  
- Normalização de setor em memória (diacríticos).  
- Auditoria de uploads; múltiplos uploads ≠ duplicidade confirmada.

## Evolução (Épico 2)

Métricas oficiais + denominadores honestos + gráficos com metodologia.  
Taxa de absenteísmo só com horas previstas confiáveis.

## Substituição

Sempre: legado ∥ canônico → diff → aprovação → ativar um gráfico/KPI por vez.

## Documentos analíticos existentes

- `docs/analytics/A01_CANONICAL_METRICS_CONTRACT.md`  
- `docs/analytics/A02_DATA_QUALITY_CONTRACT.md`  
- `docs/analytics/A02_IQB_METHODOLOGY.md`  
- `docs/analytics/A02_NORMALIZATION_CATALOG.md`
