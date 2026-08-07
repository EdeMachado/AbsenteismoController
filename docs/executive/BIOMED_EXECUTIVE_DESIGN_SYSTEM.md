# BioMed Executive Design System

Fonte canônica de tokens: `frontend/static/css/biomed-executive.css`.

## Princípios

- Corporativo premium (Fabric / Power BI Premium + identidade BioMed)
- Alta densidade com whitespace e hierarquia clara
- Sem dark mode nesta sprint (tokens `[data-theme="dark"]` reservados)
- Cores semânticas só para melhora / estabilidade / atenção / piora / risco
- Evitar visual de planilha, Bootstrap genérico ou painel excessivamente colorido

## Tokens

| Token | Uso |
|-------|-----|
| `--bm-brand` | Marca BioMed / CTAs primários |
| `--bm-accent` | Destaque secundário (gráficos) |
| `--bm-bg` / `--bm-bg-accent` | Fundo atmosférico claro |
| `--bm-surface` | Cards / painéis |
| `--bm-ink*` | Tipografia |
| `--bm-improve` / `--bm-stable` / `--bm-attention` / `--bm-worsen` / `--bm-risk` | Semântica |
| `--bm-shadow` / `--bm-radius` / `--bm-space-*` | Elevação e ritmo |
| `--bm-font` (DM Sans) / `--bm-display` (Fraunces) | Tipografia |

## Componentes

- KPI cards (`.bm-kpi`)
- Badges de tendência (`.bm-badge-*`)
- Chart containers (`.bm-chart`)
- Insight / narrativa
- Action table / cards
- Methodology drawer (`.bm-drawer-note`)
- Filters / period selector
- Skeleton / empty / error / loading
- Focus ring (`--bm-focus`)

## Acessibilidade e mobile

- Contraste em superfície clara
- Focus visível em inputs/botões
- Shell colapsa navegação abaixo de 820px
- KPI grid responsivo (5 → 3 → 2 colunas)

## Ícones

Preferir tipografia e badges textuais nesta sprint; ícones só se já existirem no shell legado.
