# ABSENTEISMOCONTROLLER — NAVIGATION & UX AUDIT

## 1. Famílias de menu (inconsistentes)

| Família | Páginas | Itens |
|---------|---------|-------|
| A — App moderno | index (estático), configuracoes | Dashboard, Clientes, Apresentação, Upload, Meus Dados, Funcionários, Comparativos, Config |
| A+ — via `menu.js` | quando JS reescreve nav | Familia A **+ Produtividade** |
| B — Legado stubs | preview, analises, tendencias | Dashboard, Upload, Preview, Análises, Tendências, Apresentação |
| C — Parcial | funcionarios, comparativos | Subconjunto sem Clientes/Dados/Config |
| D — Custom | upload_inteligente | Sidebar própria escura |

## 2. Achados de navegação

### ABS-NAV-001 — Drift menu.js vs HTML
`menu.js` injeta Produtividade; HTML estático do dashboard não lista. Usuário vê menus diferentes conforme a página.

### ABS-NAV-002 — Páginas órfãs
`upload_inteligente`, `dashboard_powerbi`, `auto_processor`, `inss`, `download_app`, `baixar_icone` fora do menu principal.

### ABS-NAV-003 — Link morto `/dashboard`
Em `download_app.html` (rota correta do dash é `/`).

### ABS-NAV-004 — Rotas HTML sem backend
`/inss`, `/download_app`, `/baixar_icone` — arquivos existem, FastAPI não registra.

### ABS-NAV-005 — Stubs no produto
Análises / Tendências / Preview “em desenvolvimento” ainda acessíveis.

### ABS-NAV-006 — Mobile: sidebar sem toggle
Exceto dashboard (PR #1), páginas autenticadas com sidebar ficam inavegáveis <1024px.

## 3. UX / visual

| Tema | Achado |
|------|--------|
| Design system | Não há; CSS variables em `:root` + muito estilo inline |
| Biblioteca UI | Nenhuma (Font Awesome CDN) |
| Tema escuro | Código parcial; comentários desabilitam em auth |
| Emojis no menu | Misturados com ícones FA — inconsistente |
| Densidade | Dashboard muito denso (muitos gráficos) |
| Feedback | Spinners pontuais; erros muitas vezes só `console` |
| Acessibilidade | Sem foco sistemático em ARIA; contraste variável |
| Loading/empty | Parcial (no-data CSS existe) |

### ABS-UX-001 — Estilos inline massivos
Dificulta tema e responsividade uniforme.

### ABS-UX-002 — Cards KPI com hover translate
Pode causar jitter em touch.

### ABS-UX-003 — Sem design tokens além de CSS vars básicas
Cores primary/secondary definidas; páginas custom sobrescrevem.

## 4. Proposta de reorganização do menu (NÃO IMPLEMENTAR)

**Operação diária**
1. Dashboard  
2. Upload  
3. Meus Dados  
4. Funcionários  

**Análise**
5. Apresentação  
6. Comparativos  
7. Produtividade  

**Cadastros / Admin**
8. Clientes  
9. Configurações  

**Ocultar do menu principal (até prontos):** Análises, Tendências, Preview, Upload Inteligente, Dashboard PowerBI, Auto Processor, INSS, Download App.

Perfis sugeridos (futuro): Admin, Cliente/RH, Saúde ocupacional (leitura clínica restrita), Diretoria (só apresentação/dashboard).
