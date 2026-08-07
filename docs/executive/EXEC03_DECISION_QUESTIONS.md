# EXEC-03 — Decision Questions

Atalhos executivos (rule engine, sem LLM).

| ID | Pergunta | Maps to (análises) |
|----|----------|-------------------|
| maior_problema | Qual é o maior problema? | setores_dias, pareto_cid_dias, custo_absenteismo |
| doenca_impacta | Qual doença mais impacta? | pareto_cid_dias/eventos, custo_cid |
| setor_concentra | Qual setor concentra o problema? | setores_*, custo_setor |
| quando_ocorre | Quando ocorre mais? | evolucao_eventos, dia_semana, faixa_horaria |
| recorrencia | Quem apresenta maior recorrência? | recorrencia (**agregado**; sem ranking nominal) |
| quanto_custa | Quanto custa? | custo_absenteismo, custo_evolucao |
| o_que_mudou | O que mudou? | tendencia_baseline, comparativo_baseline |
| biomed_realizou | O que a BioMed realizou? | biomed_producao/cobertura/execucao |
| o_que_funcionou | O que funcionou? | efetividade, antes_depois |
| pendente | O que está pendente? | condicionantes |
| fazer_agora | O que devemos fazer agora? | plano_acao / recomendações |

API: `GET /api/executive/questions` · `GET /api/executive/questions/{qid}`  
UI: módulo **Perguntas** no Command Center.

Código: `backend/executive/questions.py`.
