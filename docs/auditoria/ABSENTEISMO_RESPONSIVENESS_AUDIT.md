# ABSENTEISMOCONTROLLER — RESPONSIVENESS AUDIT

## Contexto

Há PR aberto (#1) na branch `cursor/dashboard-responsive-scroll-f8f5` que **já corrige parcialmente** o dashboard (`overflow-x: auto`, grids `.charts-grid-*`, hamburger só em `index.html`).  
`origin/main` ainda contém `body { overflow-x: hidden }` e grids fixos no dashboard.

Esta auditoria considera o **estado em disco** (feature branch + working tree).

---

## Breakpoints avaliados (análise estática)

320, 360, 375, 390, 412, 768, 1024, 1280, 1366, 1440, 1920 — via CSS/HTML (sem bateria E2E visual completa nesta rodada).

---

## Matriz por página

| ID | Página | Rota | Viewport | main.css | Hamburger | Grids fixos | Overflow | Responsiva? | Prioridade |
|----|--------|------|----------|----------|-----------|-------------|----------|-------------|------------|
| P01 | Dashboard | `/` | Sim | Sim | **Sim** (branch) | Classes OK; JS ainda força 2 colunas em casos | Melhorado | Parcial | P1 |
| P02 | Clientes | `/clientes` | Sim | Sim | N/A (layout próprio) | Inline 2 colunas | Cards/modais | Parcial | P1 |
| P03 | Upload | `/upload` | Sim | Sim | Não (no-sidebar) | Não | Baixo | Aceitável | P2 |
| P04 | Upload inteligente | `/upload_inteligente` | Sim | Sim | Não | Sidebar fixa 250px | `overflow:hidden` | **Não** | P1 |
| P05 | Dados PowerBI | `/dados_powerbi` | Sim | Sim | Não | — | Table scroll | Parcial | P1 |
| P06 | Produtividade | `/produtividade` | Sim | Sim | Não | — | Tabelas largas | Parcial | P1 |
| P07 | Funcionários | `/funcionarios` | Sim | Sim | **Não** | `repeat(3,1fr)` | Sidebar fixa mobile | **Não** | P0 |
| P08 | Comparativos | `/comparativos` | Sim | Sim | **Não** | `1fr 1fr` | Sidebar fixa | **Não** | P0 |
| P09 | Configurações | `/configuracoes` | Sim | Sim | **Não** | — | Sidebar | **Não** | P0 |
| P10 | Apresentação | `/apresentacao` | Sim | Sim | N/A fullscreen | 3 colunas | overflow hidden slides | Desktop-first | P2 |
| P11 | Perfil funcionário | `/perfil_funcionario` | Sim | Sim | **Não** | — | Sidebar | **Não** | P0 |
| P12 | Preview | `/preview` | Sim | Sim | Não | — | Stub | **Não** | P3 |
| P13 | Análises | `/analises` | Sim | Sim | Não | — | Stub | **Não** | P3 |
| P14 | Tendências | `/tendencias` | Sim | Sim | Não | — | Stub | **Não** | P3 |
| P15 | Dashboard PowerBI | `/dashboard_powerbi` | Sim | Sim | Não | 3–4 colunas | overflow hidden | **Não** | P1 |
| P16 | Auto processor | `/auto_processor` | Sim | **Não** | Não | — | overflow hidden | Parcial | P2 |
| P17 | Download app | (sem rota) | Sim | Sim | Não | — | Sidebar | **Não** | P2 |
| P18 | INSS | (sem rota) | Sim | Sim | Não | 2 colunas; table min 1200px | Tem MQ | Parcial | P2 |
| P19 | Baixar ícone | (sem rota) | Sim | Não | N/A | — | Utility | OK | P3 |
| P20 | Landing | `/landing` | Sim | Sim | N/A | — | Marketing | OK | P3 |
| P21 | Login | `/login` | Sim | Sim | N/A | — | Auth | OK | P3 |

---

## Achados de responsividade

### ABS-RESP-001 — Overflow horizontal desabilitado (main)
- **Onde:** `main` → `body { overflow-x: hidden }`
- **Efeito:** Conteúdo do dash corta sem barra lateral; usuário usa Ctrl− e perde usabilidade
- **Status branch:** corrigido para `overflow-x: auto` no PR #1
- **Prioridade:** P0 em produção (main)

### ABS-RESP-002 — Hamburger só no dashboard
- **Evidência:** Apenas `index.html` inclui `menu-toggle` + `#sidebar` + overlay + `mobile-menu.js`
- **Impacto:** Em ≤1024px, sidebar some e **não há como abrir o menu** nas demais páginas
- **Prioridade:** P0

### ABS-RESP-003 — Grids Chart.js / HTML com colunas fixas
- **Arquivos:** `funcionarios.html`, `comparativos.html`, `dashboard_powerbi.html`, `dashboard.js` (grids dinâmicos)
- **Causa:** `grid-template-columns: repeat(2|3, 1fr)` inline sem media query
- **Prioridade:** P1

### ABS-RESP-004 — Sidebar 340px em notebooks
- **Arquivo:** `main.css` `--sidebar-width: 340px`
- **Branch:** reduz para 280px entre 1025–1366
- **Prioridade:** P1

### ABS-RESP-005 — Tabelas largas
- **INSS** `min-width: 1200px`; produtividade consolidado sem wrapper consistente
- **Recomendação:** scroll horizontal controlado + cards no mobile (não só reduzir fonte)
- **Prioridade:** P1

### ABS-RESP-006 — Upload inteligente / shells próprios
- Sidebar 250px não colapsa; não usa padrão global
- **Prioridade:** P1

### ABS-RESP-007 — Apresentação desktop-locked
- `overflow: hidden`, slides 100vh — inadequado a mobile (aceitável se uso for projeção)
- **Prioridade:** P2

---

## Critérios de aceite futuros (não implementados nesta fase)

Ver seção 20 do prompt mestre: sem scroll indevido, menus mobile, touch targets, gráficos não cortados, sem regressão de cálculo/permissão.
