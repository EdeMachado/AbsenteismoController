# ABSENTEISMOCONTROLLER — CALCULATION AUDIT

## Princípio

Nenhuma fórmula foi alterada nesta auditoria.

## Fonte dos dados

Planilha → `excel_processor.py` → colunas `dias_atestados`, `horas_perdi`, `horas_dia`, espelhadas em campos legado.

## Indicadores

| ID | Indicador | Fórmula encontrada | Onde | Riscos | Prioridade |
|----|-----------|-------------------|------|--------|------------|
| ABS-CALC-001 | Dias perdidos | `SUM(dias_atestados)` | `analytics.metricas_gerais` | Sem dedupe de sobreposição; reupload do mesmo mês acumula | P1 |
| ABS-CALC-002 | Horas perdidas (KPI dash) | `SUM(horas_perdi)` sem fallback | `metricas_gerais` | Pode zerar se planilha só tiver dias | P1 |
| ABS-CALC-003 | Horas (gráficos RO) | Se sum horas=0 → `dias * horas_dia` | métodos horas RO | Inconsistência KPI vs gráfico; 44h/semana fixo | P1 |
| ABS-CALC-004 | Nº atestados | `COUNT(id)` | analytics | Conta linhas, não eventos únicos | P2 |
| ABS-CALC-005 | Funcionários afetados | `COUNT DISTINCT nomecompleto` | analytics | Identidade frágil | P1 |
| ABS-CALC-006 | Taxa absenteísmo | `(dias)/(n_func_com_atestado * 22)*100` | `taxa_absenteismo_mensal` **não usada no dash** | Denominador errado (deveria ser headcount total) | P1 |
| ABS-CALC-007 | Taxa em alertas | `(dias)/dias_uteis*100` | `alert_service` | Outra fórmula; sem headcount | P1 |
| ABS-CALC-008 | TOP CIDs | group por nome doença; exclui CIDs Z genéricos | `top_cids` | Ordena por frequência, não dias; spelling split | P2 |
| ABS-CALC-009 | TOP setores | group `setor` por count | `top_setores` | — | P2 |
| ABS-CALC-010 | TOP funcionários | group nome por **sum dias** | `top_funcionarios` | Métrica diferente do TOP setores | P2 |
| ABS-CALC-011 | Comparativo mês | último mês com dados vs anterior | `comparativo_periodos` | OK relativo | P2 |
| ABS-CALC-012 | Comparativo trimestre | calendário `now()` | mesmo | Base diferente do mensal | P2 |
| ABS-CALC-013 | Centro de custo | group por **setor** | `dias_perdidos_por_centro_custo` | Nome engana; não usa `centro_custo` | P1 |
| ABS-CALC-014 | Produtividade | soma campos manuais | tabela `produtividade` | Não deriva de atestados; campo `absenteismo` manual | P2 |
| ABS-CALC-015 | Semanas perdidas | horas/44 | RO | Jornada padrão arbitrária | P2 |

## Hipóteses técnicas não validadas em runtime

- Não há tratamento explícito de afastamentos contínuos/prorrogados.
- Não há reconciliação horas vs dias × jornada no KPI principal.
- Custo estimado de absenteísmo: **não encontrado** como cálculo padrão.
- Gravidade/incidência/prevalência clássicas de medicina do trabalho: **não implementadas** com nomenclatura formal.

## Recomendação (sem implementar)

Documentar glossário oficial de indicadores; unificar taxa; incluir headcount cadastrado; impedir double-count por `mes_referencia`+hash de linha; alinhar KPI horas com fallback dos gráficos.
