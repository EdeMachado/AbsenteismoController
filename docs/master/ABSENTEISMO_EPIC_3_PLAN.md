# Épico 3 — Biomed Insight

## Objetivo

Transformar fatos agregados validados em apoio à decisão: motor de regras → payload seguro → insight → plano de ação → (depois) IA narrativa.

## Pré-requisitos

- Épico 2 com métricas oficiais estáveis o suficiente para alimentar regras.  
- Guard anti-PII maduro.

## Escopo

- ≥30 regras determinísticas (§29).  
- Payload seguro (§30).  
- Separação fato / hipótese / recomendação / limitação.  
- Tipos de insight (§32).  
- Módulo de plano de ação (§34).  
- IA narrativa **somente após** regras (§35), sem criar números.

## Proibições

Diagnosticar, acusar fraude, nexo automático, demissão, “trabalhador problema”, disciplina, grupos pequenos, misturar saúde×desempenho.

## Critérios de aceite

- Payload sem PII (testes).  
- Regras reproduzíveis com ID e limiares.  
- Validação humana obrigatória para ações.  
- Testes §36.  
- PR draft; sem merge/deploy sem autorização.

## Backlog (resumo)

| ID | Item |
|----|------|
| E3-01 | Catálogo de regras v1 |
| E3-02 | Avaliador de regras |
| E3-03 | Builder de payload |
| E3-04 | Templates de insight |
| E3-05 | Plano de ação CRUD |
| E3-06 | Guardrails + testes PII |
| E3-07 | IA narrativa (fase 2 do épico) |
