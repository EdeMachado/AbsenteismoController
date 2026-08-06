# ABSENTEISMOCONTROLLER — TECHNICAL DEBT REGISTER

## Dívida estrutural

| ID | Item | Evidência | Impacto | Prioridade |
|----|------|-----------|---------|------------|
| ABS-CODE-001 | `main.py` ~6k linhas sem routers | `backend/main.py` | Risco de regressão | P1 |
| ABS-CODE-002 | Menus HTML triplicados | várias páginas | UX/nav | P1 |
| ABS-CODE-003 | Estilos inline massivos | `index.html`, etc. | Responsividade | P1 |
| ABS-CODE-004 | AuditService morto | sem imports | LGPD | P1 |
| ABS-CODE-005 | reportlab fora do requirements | import em generators/testes | Build | P1 |
| ABS-CODE-006 | Sem lint/typecheck/CI | repo | Qualidade | P1 |
| ABS-CODE-007 | Sem pytest suite | scripts soltos | Regressão | P1 |
| ABS-CODE-008 | `console.log` abundante (~189 hits JS) | frontend/static/js | Ruído/segurança | P3 |
| ABS-CODE-009 | `print` abundante (~278 hits Python) | backend | Logs sujos | P3 |
| ABS-CODE-010 | Dezenas de MD operacionais na raiz | `/workspace/*.md` | Ruído documental | P3 |
| ABS-CODE-011 | Hardcode Nilceia/client 2 | `main.py` startup | Manutenção/segurança | P0 |
| ABS-CODE-012 | Páginas stub mantidas | analises/tendencias/preview | Confusão | P2 |
| ABS-CODE-013 | INSS UI sem API | `inss.js` vs main.py | Feature morta | P1 |
| ABS-CODE-014 | auth.js.bak vs auth.js | working tree | Quebra runtime | P0 |
| ABS-CODE-015 | Token key `token` vs `access_token` | `inss.js` | Auth falha | P2 |
| ABS-BUILD-001 | Sem pipeline CI | — | Deploy manual frágil | P1 |
| ABS-BUILD-002 | Ambiente auditoria sem `.env`/DB | validar_seguranca falhou | Ops | P1 |
| ABS-TEST-001 | Testes PDF/isolamento não automatizados | raiz | — | P2 |

## Código morto / órfão (candidatos — não excluir sem análise)

- `ColaboradorINSS` sem rotas
- HTML `inss`, `download_app`, `baixar_icone` sem rotas
- `/relatorios` comentado
- `dashboard_powerbi` fora do menu
- Docs de deploy duplicados

## Dependências

- Pinagens razoáveis no FastAPI stack
- `pandas`/`openpyxl` com floor versions
- Falta: gunicorn, reportlab, tooling de lint
- Sem `npm audit` (não há package.json do app)
