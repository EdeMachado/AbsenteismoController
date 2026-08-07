# EXEC-03 — Absenteeism Cost Model

## Fórmula

```
CUSTO_ESTIMADO = HORAS_PERDIDAS × CUSTO_HORA
```

## Base de horas (sem double counting)

| Estado | Quando | Regra |
|--------|--------|-------|
| `registradas` | `horas_perdidas_registradas > 0` | Usa só horas registradas. **Não** soma dias convertidos. |
| `estimadas` | Horas MetricService estimadas **ou** `dias × jornada` válida | Só se registradas indisponíveis. |
| `indisponiveis` | Sem horas nem jornada válida | Custo não calculável. |

## Premissa de custo hora (`Hourly Labor Cost Assumption`)

| Estado | Origem | Linguagem |
|--------|--------|-----------|
| `REAL` | Empresa / fixture experimental `EXECUTIVE_HOURLY_COST_REAL` | “sob a premissa de custo hora informada pela empresa” |
| `ESTIMADO` | `EXECUTIVE_HOURLY_COST_ESTIMADO` | custo médio estimado informado |
| `ILUSTRATIVO` | Staging (`EXECUTIVE_STAGING_DEMO` + `EXECUTIVE_ILLUSTRATIVE_HOURLY_COST`, default 35) | **Premissa ilustrativa — substitua pelo custo hora real** |
| `NAO_INFORMADO` | Default produção | Impacto financeiro não calculável |

Rotulo UI: **“Custo médio da hora de trabalho”** (não “salário/hora”).

## O que NÃO fazer

- Não dizer “a empresa perdeu R$ X”.
- Não usar default ilustrativo como dado real de produção.
- Não inventar custos indiretos (HE, substituição, turnover, presenteísmo) sem dados.
- Sem migration de produção nesta etapa — persistência futura por empresa/unidade/CC/cargo.

## Breakdown

- Custo por CID / setor / centro de custo: alocação proporcional por participação em **dias** (proxy), documentada.
- Evolução mensal: horas mensais × taxa, ou alocação por eventos se horas mensais ausentes.
- Custo evitado / waterfall: só quando metodologia válida (preparado, não inventado).

## BioMed × resultado × custo

Variação de horas na janela comparável pode ser traduzida em impacto laboral evitado estimado **sem causalidade exclusiva**.

Código: `backend/executive/cost_model.py` · wiring em `exec03_enrichment.build_cost_block`.
