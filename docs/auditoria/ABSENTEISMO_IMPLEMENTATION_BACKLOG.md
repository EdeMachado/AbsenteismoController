# ABSENTEISMOCONTROLLER — IMPLEMENTATION BACKLOG

> Estimativas relativas (S/M/L/XL). **Não implementar nesta fase.**

## Fase 0 — Segurança e preservação

| ID | Item | Arquivos | Risco correção | Aceite | Est. | Pri |
|----|------|----------|----------------|--------|------|-----|
| B0.1 | Backup DB + código + baseline git tag | ops | Baixo | Backup restaurável | S | P0 |
| B0.2 | Restaurar `auth.js` no working tree | `frontend/static/js/auth.js` | Baixo | Arquivo presente e servido | S | P0 |
| B0.3 | Autenticar todas as rotas `/api/*` sensíveis | `main.py` | Médio (quebra clients sem token) | 401 sem JWT; smoke login | L | P0 |
| B0.4 | Remover/bloquear seed admin123 em produção | `main.py` | Médio | Sem default em prod | S | P0 |
| B0.5 | CORS allowlist domínio | `main.py` | Baixo | Só domínio oficial | S | P0 |
| B0.6 | Corrigir modelo permissão (NULL ≠ all) | `main.py`, users | **Alto** (muda quem vê o quê) | Apenas admin cross-tenant | M | P0 |
| B0.7 | Remover hardcode Nilceia | `main.py` | Médio | Permissões via UI/admin | S | P0 |
| B0.8 | Proteger `/api/backup/list` | `main.py` | Baixo | Admin only | S | P0 |
| B0.9 | SECRET_KEY obrigatória em produção | `auth.py` | Baixo | Fail-fast sem key | S | P0 |

## Fase 1 — Build e funcionamento básico

| ID | Item | Arquivos | Aceite | Est. | Pri |
|----|------|----------|--------|------|-----|
| B1.1 | Adicionar reportlab (ou remover uso) | requirements / report_generator | Import OK | S | P1 |
| B1.2 | Registrar ou remover rotas INSS/download/ícone | main.py / frontend | 404 ou feature OK | M | P1 |
| B1.3 | Unificar menu (uma fonte) | menu.js + HTMLs | Mesmos itens em todas páginas | M | P1 |
| B1.4 | Corrigir link `/dashboard` | download_app.html | Vai para `/` | S | P1 |
| B1.5 | Export com validar_acesso_client_id | main.py | 403 cross-tenant | S | P1 |
| B1.6 | Introduzir CI básico (compile + validar_seguranca) | `.github/workflows` | Pipeline verde | M | P1 |

## Fase 2 — Responsividade estrutural

| ID | Item | Arquivos | Aceite | Est. | Pri |
|----|------|----------|--------|------|-----|
| B2.1 | Merge/avaliar PR #1 responsivo dash | css/index | Critérios scroll/menu dash | M | P1 |
| B2.2 | Hamburger + overlay em todas páginas com sidebar | htmls + mobile-menu.js | Menu mobile OK | M | P0 |
| B2.3 | Classes charts-grid globais; remover inline 2/3 | várias | Sem overflow 1280/768/390 | M | P1 |
| B2.4 | Tabelas: wrapper scroll + padrão mobile cards | css + páginas dados | Critérios seção 20 | L | P1 |
| B2.5 | Padronizar shells (eliminar sidebars custom) | upload_inteligente, etc. | Um layout | L | P2 |

## Fase 3 — Responsividade por módulo

Dashboard, funcionários, comparativos, dados_powerbi, produtividade, apresentação (projeção), configurações, clientes — um módulo por PR pequeno.

## Fase 4 — Navegação e UX

Menu proposto (doc NAV), empty states, feedback erros, remover stubs do menu, acessibilidade básica.

## Fase 5 — Dados e indicadores

| ID | Item | Aceite | Pri |
|----|------|--------|-----|
| B5.1 | Glossário oficial de KPIs | Doc aprovado | P1 |
| B5.2 | Unificar taxa absenteísmo + headcount | Fórmula única documentada | P1 |
| B5.3 | Alinhar horas KPI com fallback | Dash = gráficos | P1 |
| B5.4 | Evitar double count reupload mês | Política replace/version | P1 |
| B5.5 | Corrigir “centro de custo” usar campo certo | Chart label/dados | P1 |

## Fase 6 — Segurança e LGPD

Perfis (RH vs saúde), audit log em escritas/leituras clínicas, minimização `dados_originais`, criptografia em repouso (estudo), retenção, DPA.

## Fase 7 — Qualidade e testes

pytest isolamento + auth matrix; Playwright responsivo nos viewports do prompt; testes de permissão cross-tenant.

---

## Primeira intervenção recomendada

1. **B0.2** restaurar `auth.js`  
2. **B0.1** backup  
3. **B0.3 + B0.6 + B0.4 + B0.5** (pacote segurança mínimo)  
4. **B2.2** hamburger global (desbloqueia uso mobile)  
5. Só então evoluir PR #1 de responsividade do dashboard para o restante
