# Épico 2 — Biomed Intelligence Engine, Dashboard 2.0 e UX/UI Modernization

## Objetivo

Motor central de inteligência; frontend apenas consome. Substituição gradual de gráficos via shadow.

Inclui frente obrigatória **`UX/UI Modernization`**: modernizar identidade visual, simplificar navegação e elevar usabilidade em todas as telas — **sem redesign big bang**.

## Pré-requisitos

- Épico 1 entregue tecnicamente (ou ao menos camada canônica #5/#6 em `main`).  
- Denominadores (headcount/horas previstas) tratados com honestidade metodológica.
- Responsividade baseline (PR #3) preservada.

## Escopo — Intelligence / Dashboard

- Extrair/expandir services: recurrence, trend, severity, frequency, pareto, comparison, intelligence_engine.  
- Métricas oficiais (lista do master plan §20).  
- Taxa de absenteísmo **somente** com denominador confiável.  
- Novos gráficos (§23) com metadados obrigatórios (§24).  
- Shadow legado vs novo por gráfico; ativação um a um.

## Escopo — UX/UI Modernization (obrigatório)

Detalhamento completo: `ABSENTEISMO_UX_UI_MODERNIZATION_ADDENDUM.md`.

### UX

Auditar jornadas; consolidar menus; eliminar navegação duplicada; organizar IA; páginas órfãs; menos cliques; ações primárias/secundárias; breadcrumbs; filtros; empty/loading/sucesso/erro; validação; confirmação destrutiva; acessibilidade; manter responsividade.

### UI — design system leve

Tokens (cor, tipografia, espaçamento) + componentes: botões, inputs, selects, tabelas, cards, modais, badges, alertas, tooltips, menus, cabeçalhos, filtros, gráficos, status.

### Identidade

Transmitir saúde, confiança, inteligência, segurança, tecnologia e clareza. Evitar excesso de cor, gradientes decorativos, animação excessiva, ícones sem função, dashboards carregados, baixo contraste, texto pequeno e sobrecarga informacional.

### Gráficos

Padronizar título, subtítulo, legenda, cores semânticas, unidade, tooltip, fonte, período, metodologia, empty state, alerta de baixa qualidade e supressão de grupos pequenos. **Cores não julgam clinicamente nem disciplinarmente pessoas.**

### Acessibilidade (progressivo)

Contraste, teclado, foco, labels, mensagens ligadas a campos, toque mínimo, mobile, `prefers-reduced-motion`, cor + texto/ícone.

### Estratégia de rollout

1. inventário → 2. tokens → 3. componentes-base → 4. página-piloto → 5. validação → 6. expansão gradual.

**Página-piloto recomendada:** fluxo de ingestão inteligente (Épico 1), interface nova que não afeta o upload atual. Em seguida, aplicar o DS aos módulos existentes no Épico 2.

## Fora de escopo

- IA generativa.  
- Troca simultânea de todos os gráficos.  
- Inventar headcount.  
- Redesign big bang do frontend.  
- Substituir o upload legado como piloto visual.

## Critérios de aceite

- Dashboard não recalcula regra de negócio crítica no JS.  
- Cada gráfico: fórmula, unidade, limitações, LGPD.  
- Divergências shadow documentadas.  
- Testes §26.  
- Auditoria UX + mapa de navegação + tokens + biblioteca + piloto + screenshots + checklist a11y + plano de migração visual + testes responsivos.  
- PR draft; ativação gradual; rollback por gráfico / por flag de UI.  
- Sem merge ou deploy automático.

## Backlog (resumo)

| ID | Item |
|----|------|
| E2-01 | Contratos de métricas oficiais |
| E2-02 | Headcount/denominadores (modelo + ingestão) |
| E2-03 | Intelligence engine fachada |
| E2-04–E2-18 | Gráficos 1–15 em shadow |
| E2-19 | Substituição gradual + feature flags |
| E2-20 | Testes + screenshots locais |
| E2-UX-01 | Auditoria UX + mapa de navegação |
| E2-UX-02 | Design tokens + inventário de componentes |
| E2-UX-03 | Biblioteca de componentes-base |
| E2-UX-04 | Página-piloto (ingestão inteligente) |
| E2-UX-05 | Critérios a11y + validação piloto |
| E2-UX-06 | Migração visual gradual dos módulos existentes |
| E2-UX-07 | Testes responsivos + PR draft UX/UI |
