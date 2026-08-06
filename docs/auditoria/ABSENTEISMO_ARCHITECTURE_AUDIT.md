# ABSENTEISMOCONTROLLER — ARCHITECTURE AUDIT

## 1. Visão geral

Monólito **FastAPI** que serve API REST e páginas HTML estáticas. Persistência em **SQLite** via SQLAlchemy. Frontend **sem SPA framework**: HTML + JS + CSS compartilhados. Multi-tenant por `client_id` (empresa/cliente).

```
Browser ──► FastAPI (main.py)
              ├── /api/* (JSON)
              ├── /* HTML (FileResponse)
              ├── static/ (CSS/JS)
              └── SQLite (absenteismo.db)
```

## 2. Camadas

| Camada | Local | Responsabilidade |
|--------|-------|------------------|
| Apresentação | `frontend/*.html`, `static/js/*`, `static/css/main.css` | UI, Chart.js, formulários |
| API / Orquestração | `backend/main.py` (~6148 linhas) | Todas as rotas; sem APIRouter |
| Domínio analítico | `analytics.py`, `insights.py` | KPIs e recomendações |
| Ingestão | `excel_processor.py`, upload endpoints | Planilhas → atestados |
| Relatórios | `report_generator.py`, `report_scheduler.py` | PDF/Excel/PPTX + agendamento |
| Segurança | `auth.py`, `security.py` | JWT, bcrypt, validação upload |
| Infra | `database.py`, `cache_service.py`, `backup_service.py`, `logger.py` | DB, cache, backup, logs |

## 3. Problemas arquiteturais

| ID | Problema | Impacto |
|----|----------|---------|
| ABS-CODE-001 | `main.py` monolítico sem routers | Manutenção difícil, revisões inseguras |
| ABS-CODE-002 | Menus HTML duplicados vs `menu.js` | Navegação inconsistente |
| ABS-CODE-003 | Mistura de layout: sidebar compartilhada + páginas com shell próprio | Responsividade desigual |
| ABS-CODE-004 | `AuditService` (DB) não acoplado às rotas | Auditoria só em arquivos |
| ABS-CODE-005 | Dependência `reportlab` usada mas fora do requirements | Quebra de PDF/testes |
| ABS-CODE-006 | Electron desktop separado, URL hardcoded de produção | Acoplamento deploy |

## 4. Decisões observadas

- Tenant = `Client`; dados clínicos em `Atestado` ligados via `Upload.client_id`.
- Papéis = `is_admin` + `User.client_id` (NULL = acesso a todos).
- Sem migrations Alembic: `database.py` usa helpers PRAGMA/ALTER ad-hoc.
- Cache in-memory (não compartilhado entre workers Gunicorn).

## 5. Deploy

Documentado para Hostinger (Nginx + Gunicorn + UvicornWorker). Scripts `deploy.sh`, PowerShell e dezenas de MDs operacionais na raiz (dívida documental).
