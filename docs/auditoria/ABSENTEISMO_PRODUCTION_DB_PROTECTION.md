# PROTEÇÃO DO BANCO DE PRODUÇÃO — BLOQUEIO DE DEPLOY

**Data:** 2026-08-06  
**Status:** ⛔ **DEPLOY INTERROMPIDO** até backup de produção comprovado  
**Prioridade:** Dados de produção > correção de responsividade

---

## 1. Plataforma de produção identificada

| Item | Valor |
|------|-------|
| Plataforma | **Hostinger VPS** (Nginx + app FastAPI/Uvicorn ou Gunicorn) |
| Domínio | `https://www.absenteismocontroller.com.br` |
| Evidência HTTP | Nginx 1.18.0 (Ubuntu); `/api/health` responde `status: ok`, version `2.0.0` |
| IP documentado | `72.60.166.55` |
| SSH documentado | porta `65002` (`deploy.sh`, `COMANDO_DEPLOY.txt`) |
| Diretório documentado | `~/domains/absenteismocontroller.com.br/public_html/absenteismo` (ou `/var/www/...` em guias alternativos) |
| Branch de deploy documentada | `main` via `git pull origin main` |
| Comando tipico | `ssh -p 65002 USUARIO@72.60.166.55 "cd .../absenteismo && git pull origin main"` (+ restart serviço) |

### Acesso a partir deste agente

| Canal | Resultado |
|-------|-----------|
| HTTPS health | OK |
| SSH porta 65002 | **FALHOU** — `Connection reset by peer` |
| Chaves SSH no ambiente | **Ausentes** (`~/.ssh` vazio) |

**Consequência:** não foi possível ler, fazer `PRAGMA`, nem `.backup` do SQLite de **produção** a partir deste ambiente.

---

## 2. Qual banco o código usa

Arquivo: `backend/database.py`

- Caminho **fixo no código** (não via env de URL):
  - `DB_PATH = <raiz_do_projeto>/database/absenteismo.db`
  - `SQLALCHEMY_DATABASE_URL = sqlite:///{DB_PATH}`
- Variáveis em `.env.example` (nomes): `SMTP_*`, `SECRET_KEY`, `ENVIRONMENT`
- **Não há** `DATABASE_URL` lida em `database.py` (apesar de aparecer em guia de deploy)

Portanto, em qualquer host, o banco efetivo é o arquivo  
`<cwd_do_processo>/database/absenteismo.db` relativo à instalação.

---

## 3. Diferenciação clara dos bancos

| Banco | Caminho | Tamanho | Conteúdo | É produção? |
|-------|---------|---------|----------|-------------|
| Local (Uvicorn neste workspace) | `/workspace/database/absenteismo.db` | **0,15 MB** | Quase vazio (seed local: 1 user, 5 configs, 0 atestados) | **NÃO** |
| Backup automático local | `/workspace/backups/auto_*.db` | 0,15 MB | Cópia do local | **NÃO** |
| Backup local gerado agora | `/workspace/backups/pre_responsividade_local/absenteismo_LOCAL_DEV_pre_responsividade_20260806_164407.sqlite3` | 0,15 MB | Cópia consistente local | **NÃO** |
| Produção (remoto) | No VPS: tipicamente `.../absenteismo/database/absenteismo.db` | **~3,38 MB** (via `/api/health`) | Dados reais | **SIM** |
| No repositório Git | `*.db` no `.gitignore` | — | Não versionado | — |

**Conclusão:** banco local e banco de produção **NÃO são o mesmo arquivo**.  
O local **não** serve como backup de produção.

---

## 4. Volume persistente

| Ambiente | Persistência |
|----------|--------------|
| Hostinger VPS (disco da VM) | Em geral **persistente** entre restarts e `git pull` (arquivo `.db` fora do Git) |
| Container efêmero / Render sem volume | **Não aplicável** ao modelo documentado (VPS) |
| Confirmação neste agente | **Não verificada no filesystem remoto** (sem SSH) |

Risco residual: se alguém apagar `database/` no servidor, ou fizer deploy de árvore nova sem copiar o `.db`, os dados somem. O `git pull` sozinho **não** deveria sobrescrever `.db` (está no `.gitignore`).

---

## 5–9. Integridade e backup de PRODUÇÃO

| Item | Status |
|------|--------|
| `PRAGMA quick_check` em produção | **Não executado** (sem SSH) |
| `PRAGMA integrity_check` em produção | **Não executado** (sem SSH) |
| Health remoto `integrity_check` | API reporta `true` (indício, não substitui PRAGMA local) |
| Backup produção `.backup` / snapshot | **NÃO REALIZADO** |
| SHA-256 backup produção | **N/A** |
| Caminho backup fora do deploy | **N/A — BLOQUEADOR** |

### Backup LOCAL (apenas desenvolvimento) — realizado

| Campo | Valor |
|-------|-------|
| Label | `LOCAL_DEV_ONLY_NOT_PRODUCTION` |
| Origem | `/workspace/database/absenteismo.db` |
| Arquivo | `backups/pre_responsividade_local/absenteismo_LOCAL_DEV_pre_responsividade_20260806_164407.sqlite3` |
| Tamanho | 159744 bytes |
| SHA-256 | `55aa7835e938208b4584b7202ec160332f03b79358a9d42a09d4302c9a1aae8e` |
| quick_check | `ok` |
| integrity_check | `ok` |
| journal_mode | `delete` |
| WAL/SHM | ausentes |
| Tabelas | 14 |
| Contagens | ver JSON ao lado (sem PII) |

---

## 10. Inventário local (sem dados pessoais)

| Tabela | Registros |
|--------|-----------|
| alert_rules | 0 |
| alerts | 0 |
| atestados | 0 |
| audit_logs | 0 |
| client_column_mappings | 0 |
| client_logos | 0 |
| clients | 0 |
| colaboradores_inss | 0 |
| configs | 5 |
| produtividade | 0 |
| report_schedules | 0 |
| saved_filters | 0 |
| uploads | 0 |
| users | 1 |

Produção (~3,38 MB) **certamente** contém volumes maiores; contagens remotas **não** foram lidas.

---

## 11. Riscos do código no startup / deploy

| Comando | Presente? | Risco |
|---------|-----------|-------|
| `drop_all` | **Não** encontrado | — |
| `create_all` / `init_db()` | Sim no startup | Cria tabelas **faltantes**; **não** apaga dados |
| Seed `admin`/`admin123` | Sim se admin ausente | Não apaga dados; risco de credencial padrão |
| `run_migrations` / `ensure_column` | Sim | ALTER ADD COLUMN se faltar |
| Remoção de `.db` no deploy | Não no script padrão `git pull` | OK se `.db` permanece no disco |
| Cópia de banco vazio sobre produção | **Não automatizada** neste agente | Risco humano se alguém fizer `scp` errado |

---

## 12. Plano de rollback (quando houver backup de produção)

1. Manter commit publicado atual de `main` (`33dce51` no momento da auditoria).  
2. Guardar backup: `absenteismo_producao_pre_responsividade_YYYYMMDD_HHMMSS.sqlite3` **fora** de `public_html` (ex.: `~/backups/` no VPS + cópia offsite).  
3. Restauração: parar app → substituir `database/absenteismo.db` pelo backup → verificar `PRAGMA integrity_check` → subir app → smoke `/api/health`.  
4. Não restaurar o banco **local** de 0,15 MB em produção.

---

## 13. Procedimento obrigatório no VPS (operador com SSH)

```bash
# 1) Entrar no servidor (credenciais do cliente — NÃO neste agente)
ssh -p 65002 USUARIO@72.60.166.55

# 2) Localizar o .db
cd ~/domains/absenteismocontroller.com.br/public_html/absenteismo
# ou caminho real usado pelo systemd/gunicorn
find . -name 'absenteismo.db' 2>/dev/null
ls -lah database/absenteismo.db

# 3) Integridade somente leitura
sqlite3 database/absenteismo.db 'PRAGMA quick_check;'
sqlite3 database/absenteismo.db 'PRAGMA integrity_check;'

# 4) Backup consistente
mkdir -p ~/backups/absenteismo
TS=$(date -u +%Y%m%d_%H%M%S)
OUT=~/backups/absenteismo/absenteismo_producao_pre_responsividade_${TS}.sqlite3
sqlite3 database/absenteismo.db ".backup '$OUT'"
sha256sum "$OUT"
ls -lah "$OUT"

# 5) Contagens sem PII
sqlite3 database/absenteismo.db "SELECT name FROM sqlite_master WHERE type='table';"
# COUNT(*) por tabela (sem SELECT de colunas sensíveis)
```

Copiar o backup para armazenamento **fora** do diretório de deploy (e preferencialmente offsite).

---

## 14. Confirmações

- Nenhum merge/push/PR/deploy foi feito nesta etapa.  
- Nenhum dado de produção foi alterado (sem acesso de escrita ao VPS).  
- Banco local **não** foi copiado para produção.  
- Deploy permanece **bloqueado** até backup de produção comprovado (caminho + tamanho ~3,38 MB + SHA-256 + PRAGMA ok).

## 15. Commits de preservação (código responsivo, sem publicar)

| Commit | Mensagem |
|--------|----------|
| `8392158` | `wip: preserve responsive R01 implementation` |
| `9cc48cb` | `wip: preserve responsive R01 implementation` (polish) |

Branch: `fix/production-responsive-phase-2-3` — **sem upstream / sem push**.
