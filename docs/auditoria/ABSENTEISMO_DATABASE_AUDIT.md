# ABSENTEISMOCONTROLLER — DATABASE AUDIT

## 1. Tecnologia

| Item | Valor |
|------|-------|
| SGBD | SQLite |
| ORM | SQLAlchemy 2.0 |
| Path típico | `database/absenteismo.db` (via `database.py`) |
| Migrations | Ad-hoc PRAGMA/ALTER — **sem Alembic** |
| Postgres | Não utilizado |

## 2. Tabelas / modelos

| Tabela | Modelo | Tenant | Observação |
|--------|--------|--------|------------|
| `clients` | Client | raiz | Empresa cliente |
| `uploads` | Upload | `client_id` | Planilha mensal; cascade atestados |
| `atestados` | Atestado | via upload | Dados clínicos; **sem client_id direto** |
| `users` | User | `client_id` nullable | NULL = todos |
| `configs` | Config | global | Sem tenant |
| `client_column_mappings` | ClientColumnMapping | `client_id` unique | |
| `produtividade` | Produtividade | `client_id` | Contadores manuais |
| `client_logos` | ClientLogo | `client_id` | |
| `saved_filters` | SavedFilter | `client_id` + `user_id` | |
| `audit_logs` | AuditLog | nullable | Pouco/não usado |
| `report_schedules` | ReportSchedule | `client_id` | |
| `alerts` | Alert | `client_id` | |
| `alert_rules` | AlertRule | `client_id` | |
| `colaboradores_inss` | ColaboradorINSS | `client_id` | **Sem uso de aplicação** |

## 3. Achados

### ABS-DB-001 — Multitenancy frágil (P0)
Isolamento depende de joins e disciplina de API. `Atestado` sem `client_id` dificulta RLS futuro.

### ABS-DB-002 — Cascade delete Upload → Atestados (P1)
Excluir upload apaga histórico clínico do mês. Sem soft-delete.

### ABS-DB-003 — Sem migrations versionadas (P1)
Alterações de schema manuais = drift entre ambientes.

### ABS-DB-004 — Campos duplicados legado/novo em Atestado (P2)
`dias_atestados` vs `dias_perdidos`; `horas_perdi` vs `horas_perdidas`; nomes duplicados. Risco de divergência se ingest falhar.

### ABS-DB-005 — Identidade de funcionário por nome (P1)
Sem tabela `funcionarios`; agregações por `nomecompleto` quebram com typos.

### ABS-DB-006 — Config global (P2)
Não há config por cliente (exceto cores/logos/mapping).

### ABS-DB-007 — SQLite em produção multi-usuário (P1)
Concorrência e backup/restore limitados; adequado a piloto, frágil em escala.

### ABS-DB-008 — Índices (P2)
PKs/FKs existem; ausência de índices compostos documentados para `(upload_id, cid)`, `(client_id, mes)`, etc.

## 4. Relacionamentos críticos

```
Client 1──* Upload 1──* Atestado
Client 1──* User (opcional)
Client 1──* Produtividade / Logos / Mappings / Alerts / INSS
```

## 5. Dados sensíveis

Ver `ABSENTEISMO_SECURITY_LGPD_AUDIT.md`. Campos clínicos e `dados_originais` Text merecem criptografia em repouso / minimização (não implementado).
