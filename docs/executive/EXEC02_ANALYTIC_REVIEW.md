# EXEC-02 — Revisão Analítica

## Gráficos

| Visualização | Decisão | Notas |
|--------------|---------|-------|
| Evolução temporal | **NOVO/MELHORADO** | Atual + média móvel (3) + dias; empty se <2 meses |
| Pareto CID (grupo alfabético) | **SUBSTITUI pizza** | Barras horizontais + acumulado; não capítulo oficial |
| Setores ranking | **MELHORADO** | Impacto horizontal; CC não duplicado |
| Heatmap | **NÃO nesta UI** | Só se legível; mantido no legado se útil |
| Centro de custo | **SEPARADO** | Não misturado com setor |
| Recorrência / afast. longos | **ADIADO** | Sem série canônica estável no payload atual |

## KPIs

Primários: dias, horas registradas, eventos, trabalhadores afetados.  
Secundários: duração, frequência/100 (só com efetivo), severidade, IQB.  
Sem zeros artificiais quando indisponível.

## Fontes

MetricService · DataQualityService · PerformanceService.executive_score · Rule engine.
