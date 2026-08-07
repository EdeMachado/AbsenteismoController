# Effectiveness Classification

## Headcount

Absence of headcount is **not** a global blocker. It only blocks population denominators:

- eventos por 100
- horas por 100
- frequência populacional

Absolute classifications remain available: severity control, duration, days, hours, long leaves, absolute stability.

## Prevenção de piora (this version)

Do **not** auto-classify `PREVENCAO_DE_PIORA` from stable long-leave shares.

Return `ESTABILIDADE` and hypothesis `possivel_prevencao_de_piora` (no counterfactual). Formal class requires future historical series, prior trend, documented projection, confidence interval, and expected-scenario comparison.

## Confidence

Computed from IQB, completeness, hours coverage, headcount flag, available metrics fraction, window equivalence, and conditionant penalty — see `backend/performance/confidence.py`.
