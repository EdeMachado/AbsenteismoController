# Baseline Spec

Windows: `pre_intervencao`, `30_dias`, `60_dias`, `90_dias`, `180_dias`, `12_meses`.

Each window JSON:

```json
{
  "inicio": "YYYY-MM",
  "fim": "YYYY-MM",
  "meses_esperados": 3,
  "meses_encontrados": 3,
  "completude": 1.0,
  "status": "completo|incompleto|indisponivel"
}
```

Rules:

- Incomplete periods always signaled.
- Different durations not compared without normalization (limitation emitted).
- Completeness threshold configurable (`ThresholdConfig.min_window_completeness`).
