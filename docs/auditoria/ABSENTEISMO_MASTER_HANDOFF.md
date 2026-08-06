# ABSENTEISMOCONTROLLER — MASTER HANDOFF

**Objetivo deste documento:** permitir que outro arquiteto/dev/agente continue sem o histórico do chat.

---

## 1. Finalidade do sistema

Plataforma web para **gestão e análise de absenteísmo ocupacional** por empresa (cliente): upload de planilhas de atestados, dashboards, apresentação executiva, comparativos, produtividade manual e configurações multi-usuário.

## 2. Arquitetura (resumo)

FastAPI monolítico + SQLite + frontend HTML/JS/CSS estático. Multi-tenant por `client_id`. JWT Bearer. Deploy documentado em Hostinger (Nginx/Gunicorn).

Detalhes: `ABSENTEISMO_ARCHITECTURE_AUDIT.md`

## 3. Baseline Git (no momento da auditoria)

| Item | Valor |
|------|-------|
| Repo | https://github.com/EdeMachado/AbsenteismoController |
| Branch trabalho | `cursor/dashboard-responsive-scroll-f8f5` @ `35600ac` |
| main | `33dce51` |
| PR | #1 draft (responsividade dashboard) |
| Working tree | `auth.js` **deletado**; `index.html` modificado |

## 4. Tecnologias

Python 3.12 / FastAPI 0.115 / SQLAlchemy 2 / SQLite / Chart.js / sem React.

## 5. Módulos e rotas

~21 páginas HTML, ~97 rotas HTTP. Inventário: `ABSENTEISMO_FUNCTIONAL_INVENTORY.md`.

## 6. Banco

14 modelos; tenant em `Upload.client_id` / entidades filhas. `Atestado` sem `client_id` direto. INSS schema unused.

## 7. Autenticação e perfis

- JWT 8h, bcrypt, token em `localStorage`
- `is_admin` + `client_id` (NULL = todos — **problema**)
- Hardcode startup “Nilceia” → client 2
- Seed `admin`/`admin123`

## 8. Estado atual (veredito)

Sistema **funcionalmente rico para análise de planilhas**, mas **não seguro para multiempresa em produção** sem correções P0. Responsividade **parcial** (melhor no PR #1 só no dashboard). Navegação **inconsistente**. Cálculos **úteis porém não padronizados** (taxa inconsistente/não usada).

## 9. Achados críticos (P0)

1. APIs sensíveis sem auth  
2. Permissão NULL = todos os clientes  
3. admin123 seed  
4. CORS `*`  
5. backup/list aberto  
6. auth.js ausente no working tree  
7. Mobile: menu inacessível fora do dashboard  
8. Dados de saúde (CID) expostos via client_id  

## 10. Problemas principais por área

| Área | Resumo |
|------|--------|
| Responsividade | overflow em main; hamburger incompleto; grids fixos |
| Navegação | 4 famílias de menu; órfãs; stubs |
| Segurança/LGPD | API aberta + PII/saúde |
| Banco | SQLite; sem migrations; identidade por nome |
| Cálculos | horas inconsistentes; taxa errada/não usada |
| Build/test | sem CI; reportlab faltando; validar_seguranca falhou no ambiente |

## 11. Decisões / bloqueios

- **Não alterar código funcional nesta fase** (pedido explícito do solicitante).  
- PR #1 já existe — não mergear sem revisão de segurança.  
- Não executar migrations/deploy a partir desta auditoria.

## 12. Backlog

Ver `ABSENTEISMO_IMPLEMENTATION_BACKLOG.md`. Ordem sugerida: preservar → auth.js → auth API/tenant → CORS/secrets → hamburger global → responsividade módulos → KPIs → LGPD perfis → testes.

## 13. Comandos seguros

```bash
pip install -r requirements.txt
python -m py_compile backend/main.py
python validar_seguranca.py   # requer .env e DB
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## 14. Regras para futuras implementações

1. PRs pequenos por fase/módulo.  
2. Nunca relaxar auth para “fazer funcionar”.  
3. Todo endpoint com `client_id` deve chamar `validar_acesso_client_id`.  
4. Não mudar fórmulas sem atualizar glossário + testes.  
5. Não apagar arquivos “não usados” sem grep de dependências.  
6. Responsividade: preferir reflow/scroll controlado, não só fonte menor.  
7. Credenciais e `.env` nunca no Git.

## 15. Documentos desta auditoria

1. `ABSENTEISMO_SYSTEM_BASELINE.md`  
2. `ABSENTEISMO_ARCHITECTURE_AUDIT.md`  
3. `ABSENTEISMO_FUNCTIONAL_INVENTORY.md`  
4. `ABSENTEISMO_RESPONSIVENESS_AUDIT.md`  
5. `ABSENTEISMO_NAVIGATION_UX_AUDIT.md`  
6. `ABSENTEISMO_SECURITY_LGPD_AUDIT.md`  
7. `ABSENTEISMO_DATABASE_AUDIT.md`  
8. `ABSENTEISMO_CALCULATION_AUDIT.md`  
9. `ABSENTEISMO_TECHNICAL_DEBT_REGISTER.md`  
10. `ABSENTEISMO_IMPLEMENTATION_BACKLOG.md`  
11. `ABSENTEISMO_MASTER_HANDOFF.md` (este)

## 16. Confirmação

Nenhum código funcional foi modificado para produzir esta auditoria.  
Nenhum commit/push/merge/deploy foi feito nesta fase documental.  
Arquivos criados somente em `docs/auditoria/`.
