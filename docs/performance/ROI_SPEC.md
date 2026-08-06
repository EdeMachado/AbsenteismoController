# ROI Spec

Kinds: `ROI_OBSERVADO` | `ROI_ESTIMADO` | `ROI_NAO_CALCULAVEL`

## Formula (code and docs aligned)

```
custo_total_programa = custo_programa + custos_implementacao
delta_custo_horas = (horas_baseline - horas_atuais) × custo_hora_ajustado
ROI = ((delta_custo_horas - custo_total_programa) / custo_total_programa) × 100
```

- If `delta_custo_horas > 0` → recorded as `custo_evitado`
- If `delta_custo_horas < 0` → recorded as `custo_adicional_estimado` (ROI may be negative)

## Observed ROI gates

Requires registered hours in both periods, min coverage, coverage diff within limit, equivalent methodology, equivalent periods, complete windows. Otherwise downgrade to estimated or non-calculable. Coverages appear in premises.
