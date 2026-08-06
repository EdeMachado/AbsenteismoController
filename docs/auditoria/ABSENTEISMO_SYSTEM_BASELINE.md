# ABSENTEISMOCONTROLLER — SYSTEM BASELINE

**Data da auditoria:** 2026-08-06  
**Tipo:** Diagnóstico somente leitura (sem alteração de código funcional)  
**Auditor:** Agente técnico independente (Cursor Cloud)

---

## 1. Identificação do repositório

| Item | Valor |
|------|-------|
| Repositório remoto | `https://github.com/EdeMachado/AbsenteismoController` |
| Branch atual | `cursor/dashboard-responsive-scroll-f8f5` |
| Branch principal | `main` |
| Commit HEAD (branch atual) | `35600ac8ce4b5715473048f653ddc56d94fd02b3` — *Corrige dashboard responsivo e barra de rolagem lateral* |
| Commit `origin/main` | `33dce51196865bc8c77adb841d17bcb58d78c665` — *Adicionar sistema de backup automatico e documentacao de seguranca* |
| Tags | Nenhuma |
| PR relacionado | [#1](https://github.com/EdeMachado/AbsenteismoController/pull/1) — draft — responsividade dashboard |

### Alterações locais não commitadas (no momento da auditoria)

| Status | Arquivo | Observação |
|--------|---------|------------|
| `M` | `frontend/index.html` | Diff mínimo em relação ao HEAD da feature branch |
| `D` | `frontend/static/js/auth.js` | **CRÍTICO:** arquivo removido no working tree; permanece em `auth.js.bak` e no commit HEAD |

> **Aviso:** A exclusão local de `auth.js` quebra autenticação/layout em múltiplas páginas. Não faz parte da entrega documental; deve ser restaurada do Git antes de qualquer uso (`git checkout HEAD -- frontend/static/js/auth.js`).

---

## 2. Tecnologias principais

| Camada | Tecnologia | Versão / observação |
|--------|------------|---------------------|
| Backend | FastAPI | 0.115.0 |
| ASGI | Uvicorn | 0.32.0 |
| ORM | SQLAlchemy | 2.0.36 |
| Validação | Pydantic | 2.9.2 |
| Banco | SQLite | arquivo `database/absenteismo.db` |
| Auth | JWT (python-jose) + bcrypt | HS256, 8h |
| Frontend | HTML + JS vanilla + CSS | Sem React/Vue/Angular |
| Gráficos | Chart.js 3.9.1 (CDN) | |
| Planilhas | pandas + openpyxl | |
| PDF | fpdf2 (requirements); reportlab usado em testes/código mas **ausente** do requirements |
| Desktop | Electron (`app-desktop/`) | |
| Node.js (ambiente auditoria) | v22.14.0 | Não é runtime do app web |
| npm | 10.9.7 | Sem `package.json` na raiz do app web |
| Python | 3.12.3 | |

**Framework principal:** FastAPI + frontend estático servido pelo próprio backend.  
**Não utiliza:** Tailwind, React, Next.js, Material UI, Bootstrap, shadcn, TypeScript.

---

## 3. Variáveis de ambiente (nomes apenas)

De `.env.example`:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_FROM`
- `SMTP_USE_TLS`
- `SECRET_KEY`
- `ENVIRONMENT`

Também lidas no código: `LOG_LEVEL`.

---

## 4. Comandos do projeto

| Ação | Comando |
|------|---------|
| Instalação | `pip install -r requirements.txt` |
| Desenvolvimento | `python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000` |
| Produção (docs) | Gunicorn + `uvicorn.workers.UvicornWorker` + Nginx (Hostinger) |
| Build frontend | Não aplicável (estático) |
| Lint | Não há ESLint/Ruff/Flake8 configurados |
| Testes | Scripts ad-hoc: `test_isolamento_dados.py`, `validar_seguranca.py`, `test_pdf_*.py` |
| Typecheck | Não há TypeScript / mypy configurado |

---

## 5. Contagens (baseline)

| Métrica | Quantidade |
|---------|------------|
| Páginas HTML (`frontend/*.html`) | 21 |
| Rotas HTTP (`@app.*` em `main.py`) | ~97 |
| Módulos Python em `backend/` | 24 arquivos (~15k linhas; `main.py` ~6.1k) |
| Arquivos JS em `frontend/static/js/` | 18 (+ `auth.js.bak`) |
| Modelos ORM | 14 |
| Dependências pinadas em requirements | 17 linhas |

---

## 6. Serviços externos

- SMTP (e-mail de relatórios/alertas)
- API pública de CNPJ (`/api/buscar-cnpj`)
- CDN Font Awesome + Chart.js
- Hostinger (deploy VPS documentado)
- Metabase driver SQLite em `plugins/` (integração opcional)

---

## 7. Resultado de diagnósticos seguros executados

| Comando | Resultado |
|---------|-----------|
| `python3 -m py_compile backend/main.py models.py auth.py database.py` | OK |
| `pip install -r requirements.txt` | OK |
| `import fastapi, sqlalchemy` | OK (0.115.0 / 2.0.36) |
| `import reportlab` | **FALHOU** — não está no requirements |
| `python3 validar_seguranca.py` | **FALHOU** SECRET_KEY + database path (sem `.env` / sem DB no ambiente de auditoria) |
| Lint / typecheck / build produção formal | **Não existem** no repositório |
| Suite pytest | **Não existe** |

---

## 8. Confirmação

Nenhum código funcional foi alterado nesta etapa documental.  
Documentos criados apenas sob `docs/auditoria/`.  
Sem commit, push, merge ou deploy nesta fase.
