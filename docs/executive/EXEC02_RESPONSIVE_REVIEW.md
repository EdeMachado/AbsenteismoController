# EXEC-02 — Responsividade e Acessibilidade

## Mobile (390×844)

- Menu colapsável (`bm-nav-toggle`)
- KPIs empilhados (2→1 colunas)
- Hero empilhado (score abaixo da mensagem)
- Charts com overflow-x
- Filtros empilhados, botões acessíveis

## Acessibilidade

- `:focus-visible` + tokens de foco
- `aria-label` / `aria-describedby` em charts
- Resumos textuais (`.bm-sr-only`)
- Modal metodologia com Escape / click-outside
- Não depende só de cor (badges com texto)

## Performance front

- Uma chamada `command-center` (sem fan-out redundante)
- Skeletons/status de loading
- Chart destroy ao re-render
