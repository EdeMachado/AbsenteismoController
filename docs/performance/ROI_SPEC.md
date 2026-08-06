# ROI Spec

Kinds: `ROI_OBSERVADO` | `ROI_ESTIMADO` | `ROI_NAO_CALCULAVEL`

```
ROI = ((custo_evitado - custo_programa) / custo_programa) × 100
custo_evitado = (horas_baseline - horas_atuais) × custo_hora_ajustado
```

Rules: never divide by zero program cost; never hide premises; separate registered vs estimated hours; confidence + cost source required; estimated ROI must not be presented as real savings.
