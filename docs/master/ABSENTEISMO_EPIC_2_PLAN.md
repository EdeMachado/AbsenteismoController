# Épico 2 — Biomed Intelligence Engine e Dashboard 2.0

## Objetivo

Motor central de inteligência; frontend apenas consome. Substituição gradual de gráficos via shadow.

## Pré-requisitos

- Épico 1 entregue tecnicamente (ou ao menos camada canônica #5/#6 em `main`).  
- Denominadores (headcount/horas previstas) tratados com honestidade metodológica.

## Escopo

- Extrair/expandir services: recurrence, trend, severity, frequency, pareto, comparison, intelligence_engine.  
- Métricas oficiais (lista do master plan §20).  
- Taxa de absenteísmo **somente** com denominador confiável.  
- Novos gráficos (§23) com metadados obrigatórios (§24).  
- Shadow legado vs novo por gráfico; ativação um a um.

## Fora de escopo

- IA generativa.  
- Troca simultânea de todos os gráficos.  
- Inventar headcount.

## Critérios de aceite

- Dashboard não recalcula regra de negócio crítica no JS.  
- Cada gráfico: fórmula, unidade, limitações, LGPD.  
- Divergências shadow documentadas.  
- Testes §26.  
- PR draft; ativação gradual; rollback por gráfico.

## Backlog (resumo)

| ID | Item |
|----|------|
| E2-01 | Contratos de métricas oficiais |
| E2-02 | Headcount/denominadores (modelo + ingestão) |
| E2-03 | Intelligence engine fachada |
| E2-04–E2-18 | Gráficos 1–15 em shadow |
| E2-19 | Substituição gradual + feature flags |
| E2-20 | Testes + screenshots locais |
