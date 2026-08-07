# EXEC-03 — Analytics Catalog

Catálogo de análises do Executive Analytics. Cada item responde uma pergunta objetiva.
Disponibilidade é avaliada em runtime — **nunca inventa série/campo ausente**.

| # | ID | Título | Pergunta | Campos | Privacidade |
|---|-----|--------|----------|--------|-------------|
| 01 | evolucao_eventos | Evolução mensal de eventos | QUANDO | serie_temporal | aggregate |
| 02 | evolucao_dias | Evolução mensal de dias perdidos | QUANDO | serie_temporal | aggregate |
| 03 | evolucao_horas | Evolução mensal de horas perdidas | QUANDO | serie_temporal_horas | aggregate |
| 04 | media_movel | Média móvel | QUANDO | serie_temporal | aggregate |
| 05 | tendencia_baseline | Tendência vs baseline | QUANTO | baseline | aggregate |
| 06 | pareto_cid_eventos | Pareto CID por eventos | O QUE | distribuicao_cid | aggregate |
| 07 | pareto_cid_dias | Pareto CID por dias | O QUE | distribuicao_cid | aggregate |
| 08 | pareto_cid_horas | Pareto CID por horas | O QUE | distribuicao_cid_horas | aggregate |
| 09 | grupos_cid | Distribuição por grupos CID | O QUE | distribuicao_cid | aggregate |
| 10 | setores_eventos | Setores por eventos | ONDE | distribuicao_setor | aggregate |
| 11 | setores_dias | Setores por dias | ONDE | distribuicao_setor | aggregate |
| 12 | setores_horas | Setores por horas | ONDE | distribuicao_setor_horas | aggregate |
| 13 | freq_sev_setor | Frequência × severidade por setor | ONDE | distribuicao_setor | aggregate |
| 14 | heatmap_setor_mes | Heatmap setor × mês | ONDE/QUANDO | heatmap_setor_mes | aggregate |
| 15 | centro_custo | Centro de custo | ONDE | distribuicao_centro_custo | aggregate |
| 16 | cargo | Cargo | ONDE | distribuicao_cargo | aggregate |
| 17 | dia_semana | Dia da semana | QUANDO | distribuicao_dia_semana | aggregate |
| 18 | faixa_horaria | Faixa horária | QUANDO | distribuicao_faixa_horaria | aggregate |
| 19 | duracao | Duração dos afastamentos | O QUE | distribuicao_duracao | aggregate |
| 20 | afastamentos_prolongados | Afastamentos prolongados | O QUE | afastamentos_longos | aggregate |
| 21 | recorrencia | Recorrência (agregada) | QUEM | recorrencia_agregada | aggregate |
| 22 | genero | Distribuição por gênero | QUEM | distribuicao_genero | aggregate |
| 23 | faixa_etaria | Faixas etárias | QUEM | distribuicao_faixa_etaria | aggregate |
| 24 | comparativo_baseline | Comparativo atual × baseline | QUANTO | baseline | aggregate |
| 25 | antes_depois | Antes × depois de intervenção | QUANTO | janela_intervencao | aggregate |
| 26 | biomed_producao | Produção BioMed | E AGORA | biomed_performance | aggregate |
| 27 | biomed_cobertura | Cobertura BioMed | E AGORA | biomed_performance | aggregate |
| 28 | biomed_execucao | Execução das ações | E AGORA | biomed_performance | aggregate |
| 29 | efetividade | Efetividade | E AGORA | biomed_performance | aggregate |
| 30 | iqb | Qualidade / IQB | QUANTO | iqb | aggregate |
| 31 | completude | Completude | QUANTO | iqb_dimensoes | aggregate |
| 32 | cobertura_horas | Cobertura de horas | QUANTO | cobertura_horas | aggregate |
| 33 | condicionantes | Condicionantes empresariais | E AGORA | conditionants | aggregate |
| 34 | custo_absenteismo | Custo do absenteísmo | QUANTO | custo | aggregate |
| 35 | custo_evolucao | Evolução do custo no tempo | QUANTO | custo + serie_temporal | aggregate |
| — | custo_cid | Custo por CID | QUANTO | custo + distribuicao_cid | aggregate |
| — | custo_setor | Custo por setor | QUANTO | custo + distribuicao_setor | aggregate |

## Condicionais nesta sprint

**Implementados quando dados existem:** evolução eventos/dias, média móvel, Pareto CID, setores, centro de custo, dia da semana (se `data_afastamento`), cargo (se preenchido + threshold), recorrência agregada, afastamentos ≥15d, IQB, BioMed performance, condicionantes, custo (+ evolução/CID/setor).

**Marcados indisponíveis até haver campo/série válida:** faixa horária, heatmap setor×mês, horas por CID/setor dedicadas, gênero, faixa etária, antes×depois intervenção formal, waterfall/custo evitado sem metodologia.

Código: `backend/executive/analytics_catalog.py` · avaliação em `exec03_enrichment.build_availability_flags`.
