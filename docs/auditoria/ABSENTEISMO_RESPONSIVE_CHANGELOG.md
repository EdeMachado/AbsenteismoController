# ABSENTEISMO — Changelog responsivo (produção)

## 2026-08-06 — Preparação + R01 + R02

### Baseline confirmado

- Remoto: `https://github.com/EdeMachado/AbsenteismoController`
- Branch base aproveitada: `cursor/dashboard-responsive-scroll-f8f5` @ `35600ac` (PR #1)
- `origin/main`: `33dce51`
- Branch nova: `fix/production-responsive-phase-2-3`
- Working tree antes: `auth.js` apagado; `index.html` com `<script auth.js>` comentado (acidental) — **descartado**

### Restauração auth.js

- Restaurado via Git HEAD
- SHA256: `63940a62ac88aac6e4ef8125f237732f98b95074333193588c8cfd73f19fe473`
- Sem alteração de lógica

### Decisão PR #1

Aproveitado integralmente (overflow-x auto, charts-grid, hamburger no dashboard, sidebar 280px em notebooks). Nova branch criada a partir dele para estender o shell mobile globalmente.

### Lote R01 — Estrutura global

**Arquivos:**
- `frontend/static/css/main.css` — shell R01 (header-leading, modais, forms, tabelas, grids período/comparativo, touch 44px)
- `frontend/static/js/mobile-menu.js` — injeta overlay + hamburger + ESC/swipe/resize em qualquer página com `.sidebar`
- 15+ HTMLs — inclusão de `mobile-menu.js` e `id="sidebar"` onde faltava

**Comportamento anterior:** sidebar some &lt;1024px sem botão na maioria das páginas; overflow cortado no main (já corrigido no PR #1).

**Comportamento novo:** menu móvel padronizado; containers fluidos; modais/tabelas/forms sem estouro global.

**Risco:** baixo — só CSS/JS de layout; IDs/API intactos.

### Lote R02 — Dashboard

Herdado do PR #1 + shell R01. Sem mudança de fórmulas/API.

### Fora de escopo (não alterado)

API, banco, auth logic, CORS, cálculos, permissões, INSS feature, PowerBI orphan polish completo.
