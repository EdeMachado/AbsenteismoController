# Absenteísmo Controller — AI Governance (Biomed Insight)

## Princípio

A IA **não** analisa o banco bruto. Consome apenas fatos agregados validados pelo motor de regras.

## Pipeline

```text
Métricas/IQB/alertas (backend)
  → Motor de regras determinísticas (≥30)
  → Payload seguro
  → Insight (fato / hipótese / recomendação / limitação)
  → Validação humana
  → Plano de ação
  → (opcional) IA narrativa redacional
```

## Payload permitido

`client_id`, período, métricas, variações, concentrações agregadas, qualidade, alertas, limitações, população agregada.

## Proibido no payload / saída

Nome, CPF, matrícula, e-mail, telefone, texto clínico, CID individual, prontuário, grupos abaixo do limiar LGPD.

## Proibições de conduta da IA

Diagnosticar; acusar fraude; nexo causal automático; sugerir demissão; “trabalhador problema”; decisão disciplinar; misturar saúde e desempenho; inventar números; alterar fatos.

## Confiança e auditoria

Toda saída cita metodologia interna, limitações, severidade da regra, versão do catálogo e exige validação humana antes de virar ação operacional.
