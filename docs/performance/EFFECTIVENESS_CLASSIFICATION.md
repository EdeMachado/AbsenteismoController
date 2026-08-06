# Effectiveness Classification

Codes:

- `EFICACIA_POSITIVA_INTEGRAL`
- `EFICACIA_POSITIVA_PARCIAL`
- `CONTROLE_SEVERIDADE`
- `CONTROLE_FREQUENCIA`
- `ESTABILIDADE`
- `PREVENCAO_DE_PIORA`
- `SEM_EVIDENCIA_SUFICIENTE`
- `RESULTADO_INCONCLUSIVO`
- `RESULTADO_DESFAVORAVEL`

All thresholds live in `ThresholdConfig` and are unit-tested.

Conditionants (delayed/refused structural actions) downgrade integral → partial and add limitations. **No automatic causality.**
