# Confidence Formula

```
conf = clamp01(
  0.25 * iqb_norm
+ 0.20 * completude_media
+ 0.15 * cobertura_horas_media
+ 0.10 * headcount_flag
+ 0.15 * fracao_metricas_disponiveis
+ 0.10 * equivalencia_janelas
+ 0.05 * (1 - penalidade_condicionantes)
)
```

- `iqb_norm` = IQB/100 (or 0.4 if missing)
- `headcount_flag` = 1.0 if any period has headcount else 0.6
- `equivalencia_janelas` = 1.0 if complete else 0.3
- `penalidade_condicionantes` = min(1, n_adiadas_recusadas / 3)

Implemented in `backend/performance/confidence.py`. Confidence varies with data quality — not a fixed class constant.
