# Executive Performance Score

Dimensions carry status: `avaliada` | `nao_avaliada` | `indisponivel` | `nao_aplicavel`.

Missing dimensions do **not** receive a neutral 50.

Unavailable weights are redistributed proportionally among evaluated dimensions (`pesos_efetivos` sum to 100). Returns original weights, effective weights, evaluated/not evaluated lists, score coverage, and redistribution methodology.

If coverage < `min_score_coverage` → `score=None`, `status=INSUFICIENTE`.

Delta selection uses `is not None` (preserving `0.0`), never Python `or`.

## Action execution

`execucao = executadas / aprovadas_aplicaveis` (not propostas). Zero denominator → dimension not evaluated.
