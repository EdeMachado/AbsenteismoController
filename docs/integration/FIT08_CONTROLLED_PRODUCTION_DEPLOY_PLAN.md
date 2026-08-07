# FIT-08 — Controlled Production Deploy Plan

## Status

| Item | Valor |
|------|-------|
| Decisão deste documento | **PLANO PRONTO — EXECUÇÃO NÃO AUTORIZADA AQUI** |
| Deploy automático | **PROIBIDO** |
| Acesso VPS por agente | **NÃO EXECUTADO** |
| Target `main` | `540cda0806326aa14ced57d42fd43e8a69817d08` |
| PR integrado | [#11](https://github.com/EdeMachado/AbsenteismoController/pull/11) |
| Modo | `DEPLOY_DE_CODIGO_SEM_MIGRATION=true` |

Este arquivo contém **somente** o plano humano (blocos SSH).  
**Nada foi executado em produção por este pacote.**

---

## 1. Diagnóstico do deploy

### Estado validado (pré-condições)

| Área | Evidência |
|------|-----------|
| Merge em `main` | `540cda0806326aa14ced57d42fd43e8a69817d08` (PR #11) |
| App prod | `/var/www/absenteismo` · `absenteismocontroller.service` · `127.0.0.1:8000` |
| Banco vivo | `/var/www/absenteismo/database/absenteismo.db` |
| Backup | `/root/backups/absenteismo/absenteismo_pre_fit06_20260807_000226.db` |
| Backup SHA-256 | `13c485ace101695b792ac1dd9f634cd9291ccc381b33dbaeb79f3f316acae1ff` |
| Backup checks | quick_check ok · integrity_check ok |
| Clientes | `2` CONVERPLAST · `4` RODA DE OURO |
| Acessos | 2 admins ativos · 1 tenant Converplast · 0 non-admin sem tenant · 0 senha comum |
| Env | `ENVIRONMENT=production` · flags OFF · API docs OFF · `SECRET_KEY` presente |

### Tipo de deploy

- **Somente código versionado** até o merge commit acima.
- **Sem migration**, sem SQL Epic 1, sem criar `ingestion_*`.
- **Sem** restaurar backup automaticamente.
- **Um** restart de serviço (Bloco 5), somente após import OK.

### Untracked a preservar

`database/` · `gunicorn_config.py` · `logs/` · `nohup.out` · `.env` · backups locais

### Proibido

`git clean` · `git reset --hard` · substituir `database/` · remover `logs/` / `gunicorn_config.py` / `.env` · trocar `SECRET_KEY` · ativar flags · merge adicional · deploy automático

### GO humano (só se todos)

- backup validado existe e SHA confere  
- `git status` sem modificação tracked perigosa  
- banco e `.env` preservados  
- `origin/main` / tip local após fetch = exatamente `540cda0…`  
- flags OFF · `SECRET_KEY` permanece  
- import/py_compile passam  
- rollback de código pronto (OLD_HEAD capturado)

### NO-GO (parar)

- `main` divergir do target  
- banco ausente  
- backup SHA divergir  
- `SECRET_KEY` ausente  
- tracked locais conflitarem  
- dependência/import falhar  
- migration necessária  
- flag experimental ativa  

---

## 2. Oito blocos SSH (humanos — não executar neste agente)

> Rodar **como root** (ou com sudo) no VPS, **um bloco por vez**.  
> Abortar no primeiro `exit 1`.  
> Não colar credenciais; login smoke usa prompt ou variáveis já existentes no shell do operador.

### BLOCO 1 — Pré-deploy somente leitura

```bash
#!/usr/bin/env bash
set -euo pipefail
APP=/var/www/absenteismo
TARGET=540cda0806326aa14ced57d42fd43e8a69817d08
BACKUP=/root/backups/absenteismo/absenteismo_pre_fit06_20260807_000226.db
EXPECT_BACKUP_SHA=13c485ace101695b792ac1dd9f634cd9291ccc381b33dbaeb79f3f316acae1ff
DB=$APP/database/absenteismo.db

cd "$APP"
echo "=== FIT-08 BLOCO 1 — READ ONLY ==="
echo "pwd=$(pwd)"
echo "branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo UNKNOWN)"
OLD_HEAD=$(git rev-parse HEAD)
echo "OLD_HEAD=$OLD_HEAD"
echo "--- git status --short ---"
git status --short
echo "--- origin/main (fetch info only) ---"
git fetch origin main --dry-run 2>&1 || true
git ls-remote origin refs/heads/main
echo "--- service ---"
systemctl is-active absenteismocontroller.service || true
systemctl status absenteismocontroller.service --no-pager -n 20 || true
echo "--- health ---"
curl -sS -m 5 http://127.0.0.1:8000/api/health || echo "HEALTH_FAIL"
echo
echo "--- database ---"
ls -lh "$DB"
test -f "$DB"
sqlite3 "$DB" 'PRAGMA quick_check;' | head -1
sqlite3 "$DB" 'PRAGMA integrity_check;' | head -1
echo "--- backup ---"
test -f "$BACKUP"
BACKUP_SHA=$(sha256sum "$BACKUP" | awk '{print $1}')
echo "BACKUP_SHA=$BACKUP_SHA"
test "$BACKUP_SHA" = "$EXPECT_BACKUP_SHA"
sqlite3 "$BACKUP" 'PRAGMA quick_check;' | head -1
sqlite3 "$BACKUP" 'PRAGMA integrity_check;' | head -1
echo "--- env presence (no secrets) ---"
if [ -f "$APP/.env" ]; then
  for k in ENVIRONMENT SECRET_KEY ENABLE_INTELLIGENT_INGESTION ENABLE_BIOMED_PERFORMANCE_ENGINE ENABLE_API_DOCS CORS_ALLOWED_ORIGINS; do
    if grep -Eq "^[[:space:]]*${k}=" "$APP/.env"; then
      if [ "$k" = "SECRET_KEY" ]; then echo "$k=PRESENT"; else
        v=$(grep -E "^[[:space:]]*${k}=" "$APP/.env" | tail -1 | cut -d= -f2-)
        echo "$k=$v"
      fi
    else echo "$k=ABSENT"; fi
  done
else echo ".env=ABSENT"; exit 1; fi
echo "--- critical untracked ---"
for f in database gunicorn_config.py logs nohup.out .env; do
  if [ -e "$f" ]; then echo "PRESERVE_OK $f"; else echo "MISSING $f"; fi
done
echo "TARGET_HEAD=$TARGET"
echo "BLOCO1_RESULT=OK"
echo "NOTE: anote OLD_HEAD=$OLD_HEAD para o Bloco 7"
```

### BLOCO 2 — Preparar configuração (idempotente)

```bash
#!/usr/bin/env bash
set -euo pipefail
APP=/var/www/absenteismo
TS=$(date -u +%Y%m%d_%H%M%S)
CFG_BAK=/root/backups/absenteismo/config_pre_fit08_$TS
ENVF=$APP/.env
CORS_VALUE='https://www.absenteismocontroller.com.br'

cd "$APP"
echo "=== FIT-08 BLOCO 2 — CONFIG (no SECRET_KEY change) ==="
test -f "$ENVF"
mkdir -p "$CFG_BAK"
cp -a "$ENVF" "$CFG_BAK/.env"
if [ -f "$APP/gunicorn_config.py" ]; then cp -a "$APP/gunicorn_config.py" "$CFG_BAK/gunicorn_config.py"; fi
echo "CFG_BACKUP=$CFG_BAK"

# Preserve existing SECRET_KEY; never print it.
python3 - <<'PY'
import os, re, pathlib
env_path = pathlib.Path("/var/www/absenteismo/.env")
text = env_path.read_text(encoding="utf-8")
lines = text.splitlines()
wanted = {
    "ENVIRONMENT": "production",
    "ENABLE_INTELLIGENT_INGESTION": "false",
    "ENABLE_BIOMED_PERFORMANCE_ENGINE": "false",
    "ENABLE_API_DOCS": "false",
    "CORS_ALLOWED_ORIGINS": "https://www.absenteismocontroller.com.br",
}
keys_seen = set()
out = []
for line in lines:
    m = re.match(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*)(.*)$", line)
    if not m:
        out.append(line)
        continue
    indent, key, eq, val = m.groups()
    keys_seen.add(key)
    if key == "SECRET_KEY":
        if not val.strip():
            raise SystemExit("SECRET_KEY empty — NO-GO")
        out.append(line)  # keep as-is
    elif key in wanted:
        out.append(f"{indent}{key}{eq}{wanted[key]}")
    else:
        out.append(line)
for key, val in wanted.items():
    if key not in keys_seen:
        out.append(f"{key}={val}")
if "SECRET_KEY" not in keys_seen:
    raise SystemExit("SECRET_KEY absent — NO-GO")
env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
print("ENV_UPDATED=ok")
PY

echo "--- verify presence (SECRET_KEY masked) ---"
for k in ENVIRONMENT ENABLE_INTELLIGENT_INGESTION ENABLE_BIOMED_PERFORMANCE_ENGINE ENABLE_API_DOCS CORS_ALLOWED_ORIGINS SECRET_KEY; do
  if [ "$k" = "SECRET_KEY" ]; then
    grep -Eq "^[[:space:]]*SECRET_KEY=.+" "$ENVF" && echo "SECRET_KEY=PRESENT" || { echo "SECRET_KEY=ABSENT"; exit 1; }
  else
    grep -E "^[[:space:]]*${k}=" "$ENVF" | tail -1
  fi
done
echo "ROLLBACK_CONFIG: cp -a $CFG_BAK/.env $ENVF"
echo "BLOCO2_RESULT=OK"
```

### BLOCO 3 — Atualização do código (fast-forward apenas)

```bash
#!/usr/bin/env bash
set -euo pipefail
APP=/var/www/absenteismo
TARGET=540cda0806326aa14ced57d42fd43e8a69817d08
DB=$APP/database/absenteismo.db

cd "$APP"
echo "=== FIT-08 BLOCO 3 — CODE UPDATE FF ONLY ==="
test -f "$DB"
test -f "$APP/.env"
test -f "$APP/gunicorn_config.py"

# Recusar mudanças tracked perigosas
if git status --porcelain | grep -E '^[ MADRCU]{1,2} ' | grep -vqE '^\?\?'; then
  echo "NO-GO: tracked modifications present"; git status --short; exit 1
fi

OLD_HEAD=$(git rev-parse HEAD)
echo "OLD_HEAD=$OLD_HEAD"
git fetch origin main
REMOTE_MAIN=$(git rev-parse origin/main)
echo "origin/main=$REMOTE_MAIN"
test "$REMOTE_MAIN" = "$TARGET" || { echo "NO-GO: origin/main != TARGET"; exit 1; }

git checkout main
# Fast-forward only to TARGET (fails if diverged / non-FF)
git merge --ff-only "$TARGET"
DEPLOYED_HEAD=$(git rev-parse HEAD)
echo "DEPLOYED_HEAD=$DEPLOYED_HEAD"
test "$DEPLOYED_HEAD" = "$TARGET" || { echo "NO-GO: HEAD != TARGET"; exit 1; }

# Garantir untracked críticos intactos
test -f "$DB"
test -d "$APP/database"
test -f "$APP/.env"
test -f "$APP/gunicorn_config.py"
test -d "$APP/logs" || echo "WARN: logs/ missing (non-fatal if expected)"
echo "BLOCO3_RESULT=OK"
echo "EXPORT: OLD_HEAD=$OLD_HEAD DEPLOYED_HEAD=$DEPLOYED_HEAD"
```

### BLOCO 4 — Dependências + import gate

```bash
#!/usr/bin/env bash
set -euo pipefail
APP=/var/www/absenteismo
cd "$APP"
echo "=== FIT-08 BLOCO 4 — DEPS + IMPORT ==="
test -x "$APP/venv/bin/python" || test -x "$APP/.venv/bin/python"
PY=$APP/venv/bin/python
[ -x "$PY" ] || PY=$APP/.venv/bin/python

echo "--- requirements head ---"
head -n 40 requirements.txt
echo "--- install (no blind upgrade of entire system) ---"
"$PY" -m pip install -r requirements.txt
if [ -f requirements-dev.txt ]; then
  echo "NOTE: requirements-dev.txt presente no repo; NÃO instalar em produção"
fi

echo "--- py_compile / import ---"
"$PY" -m py_compile backend/main.py backend/authz.py backend/cors_config.py backend/route_security_registry.py
ABSENTEISMO_SQLITE_PATH="$APP/database/absenteismo.db" \
ENVIRONMENT=production \
ENABLE_INTELLIGENT_INGESTION=false \
ENABLE_BIOMED_PERFORMANCE_ENGINE=false \
ENABLE_API_DOCS=0 \
"$PY" -c "import backend.main; print('import_ok', backend.main.app.title)"

echo "BLOCO4_RESULT=OK"
```

### BLOCO 5 — Restart único

```bash
#!/usr/bin/env bash
set -euo pipefail
echo "=== FIT-08 BLOCO 5 — RESTART ONCE ==="
systemctl restart absenteismocontroller.service
sleep 5
systemctl is-active absenteismocontroller.service | grep -qx active
systemctl status absenteismocontroller.service --no-pager -n 40
echo "--- journal (new) ---"
journalctl -u absenteismocontroller.service -n 80 --no-pager || true
echo "BLOCO5_RESULT=OK"
```

### BLOCO 6 — Smoke imediato

```bash
#!/usr/bin/env bash
set -euo pipefail
APP=/var/www/absenteismo
DB=$APP/database/absenteismo.db
BASE=http://127.0.0.1:8000

echo "=== FIT-08 BLOCO 6 — SMOKE ==="
HEALTH=$(curl -sS -m 8 "$BASE/api/health")
echo "HEALTH_JSON=$HEALTH"
echo "$HEALTH" | grep -qi 'ok\|healthy\|true\|status' || echo "WARN: review health payload manually"
# database healthy if field exists
echo "$HEALTH" | grep -Ei 'database|healthy' || true

echo "--- public pages ---"
for p in / /login; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' -m 8 "$BASE$p" || echo ERR)
  echo "PAGE $p -> $code"
done

echo "--- APIs without token must 401 (except login/health) ---"
for path in /api/clientes /api/atestados /api/uploads /api/usuarios; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' -m 8 "$BASE$path" || echo ERR)
  echo "ANON $path -> $code"
  case "$code" in 401|403) ;; *) echo "NO-GO unexpected $path=$code"; exit 1 ;; esac
done
code=$(curl -sS -o /dev/null -w '%{http_code}' -m 8 -X POST "$BASE/api/auth/login" -d 'username=x&password=y' || echo ERR)
echo "LOGIN_BAD -> $code (expect 401/422)"

echo "--- experimental routes off ---"
for path in /api/ingestion/preview /experimental/ingestion; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' -m 8 "$BASE$path" || echo ERR)
  echo "EXP $path -> $code"
  case "$code" in 404|401|403|405) ;; *) echo "WARN review $path=$code" ;; esac
done

echo "--- db integrity + inventory aggregates ---"
sqlite3 "$DB" 'PRAGMA quick_check;'
sqlite3 "$DB" 'PRAGMA integrity_check;' | head -1
ls -lh "$DB"
sqlite3 "$DB" "SELECT id, substr(nome,1,40) FROM clients WHERE id IN (2,4) ORDER BY id;"
sqlite3 "$DB" "SELECT client_id, COUNT(*) FROM uploads WHERE client_id IN (2,4) GROUP BY client_id ORDER BY client_id;"
sqlite3 "$DB" "SELECT client_id, COUNT(*) FROM atestados WHERE client_id IN (2,4) GROUP BY client_id ORDER BY client_id;"
sqlite3 "$DB" "SELECT COUNT(*) AS admins_active FROM users WHERE is_admin=1 AND is_active=1;"
sqlite3 "$DB" "SELECT COUNT(*) AS orphan_non_admin FROM users WHERE IFNULL(is_admin,0)=0 AND client_id IS NULL;"

echo "--- service / memory ---"
systemctl is-active absenteismocontroller.service
ps -o pid,rss,cmd -C gunicorn || ps aux | grep -E 'gunicorn|uvicorn' | grep -v grep || true

echo "NOTE: login real com credencial válida deve ser feito pelo operador sem colar senha neste log"
echo "BLOCO6_RESULT=OK"
```

### BLOCO 7 — Rollback de código (preparar — NÃO executar no deploy feliz)

```bash
#!/usr/bin/env bash
# FIT-08 BLOCO 7 — ROLLBACK DE CÓDIGO (manual / emergência)
# NÃO restaurar banco automaticamente.
# Substitua OLD_HEAD pelo valor capturado no Bloco 1/3.
set -euo pipefail
APP=/var/www/absenteismo
ROLLBACK_HEAD="${ROLLBACK_HEAD:?set ROLLBACK_HEAD to pre-deploy SHA}"
DB=$APP/database/absenteismo.db

cd "$APP"
echo "=== FIT-08 BLOCO 7 — CODE ROLLBACK ==="
test -f "$DB"
test -f "$APP/.env"
echo "CURRENT=$(git rev-parse HEAD)"
echo "ROLLBACK_HEAD=$ROLLBACK_HEAD"
git fetch origin
# Prefer checkout of exact previous SHA without clean/reset --hard
git checkout "$ROLLBACK_HEAD"
test "$(git rev-parse HEAD)" = "$ROLLBACK_HEAD"
test -f "$DB"
test -f "$APP/.env"
# Optional: restore .env from CFG_BAK if Bloco 2 broke config
# cp -a /root/backups/absenteismo/config_pre_fit08_<TS>/.env "$APP/.env"
PY=$APP/venv/bin/python; [ -x "$PY" ] || PY=$APP/.venv/bin/python
"$PY" -c "import backend.main; print('import_ok')"
systemctl restart absenteismocontroller.service
sleep 5
systemctl is-active absenteismocontroller.service
curl -sS -m 8 http://127.0.0.1:8000/api/health || true
echo "BLOCO7_RESULT=ROLLBACK_CODE_DONE"
echo "DB_RESTORE=NOT_PERFORMED"
```

### BLOCO 8 — Resultado final

```bash
#!/usr/bin/env bash
set -euo pipefail
APP=/var/www/absenteismo
TARGET=540cda0806326aa14ced57d42fd43e8a69817d08
DB=$APP/database/absenteismo.db
# Preencha OLD_HEAD com o valor do Bloco 1
OLD_HEAD="${OLD_HEAD:?export OLD_HEAD from Bloco 1}"

cd "$APP"
DEPLOYED_HEAD=$(git rev-parse HEAD)
SERVICE_STATUS=$(systemctl is-active absenteismocontroller.service || echo inactive)
HEALTH_STATUS=$(curl -sS -m 5 http://127.0.0.1:8000/api/health || echo FAIL)
DATABASE_INTEGRITY=$(sqlite3 "$DB" 'PRAGMA integrity_check;' | head -1)
CLIENT_2=$(sqlite3 "$DB" "SELECT COUNT(*) FROM clients WHERE id=2;")
CLIENT_4=$(sqlite3 "$DB" "SELECT COUNT(*) FROM clients WHERE id=4;")
FLAGS_OFF=$(
  python3 - <<'PY'
from pathlib import Path
import re
text=Path("/var/www/absenteismo/.env").read_text()
def get(k,default=""):
  m=re.search(rf"^{k}=(.*)$",text,re.M)
  return (m.group(1).strip() if m else default)
vals=[get("ENABLE_INTELLIGENT_INGESTION","false"),get("ENABLE_BIOMED_PERFORMANCE_ENGINE","false"),get("ENABLE_API_DOCS","false")]
print("yes" if all(v.lower() in ("false","0","") for v in vals) else "no")
PY
)

if [ "$DEPLOYED_HEAD" = "$TARGET" ] && [ "$SERVICE_STATUS" = "active" ] && [ "$DATABASE_INTEGRITY" = "ok" ] && [ "$CLIENT_2" = "1" ] && [ "$CLIENT_4" = "1" ] && [ "$FLAGS_OFF" = "yes" ]; then
  DEPLOY_RESULT=SUCCESS
else
  DEPLOY_RESULT=FAIL_OR_INCOMPLETE
fi

cat <<EOF
OLD_HEAD=$OLD_HEAD
TARGET_HEAD=$TARGET
DEPLOYED_HEAD=$DEPLOYED_HEAD
SERVICE_STATUS=$SERVICE_STATUS
HEALTH_STATUS=$HEALTH_STATUS
DATABASE_INTEGRITY=$DATABASE_INTEGRITY
CLIENT_2=$CLIENT_2
CLIENT_4=$CLIENT_4
FLAGS_OFF=$FLAGS_OFF
ROLLBACK_HEAD=$OLD_HEAD
DEPLOY_RESULT=$DEPLOY_RESULT
EOF
```

---

## 3. Riscos

| Risco | Mitigação |
|-------|-----------|
| Working tree prod com tracked dirty | Bloco 1/3 aborta |
| Fast-forward impossível (main divergiu) | Bloco 3 exige `origin/main == TARGET` e `--ff-only` |
| Perda de untracked | Sem `clean`/`reset --hard`; asserts pós-pull |
| Troca acidental de `SECRET_KEY` | Bloco 2 preserva linha; só verifica PRESENT |
| Flag experimental ligada | Bloco 2 força false; Bloco 8 valida FLAGS_OFF |
| Dependência quebrada | Bloco 4 para antes do restart |
| App não sobe | Bloco 5/6 → Bloco 7 rollback código |
| Corrupção de banco (improvável sem migration) | Não restaurar auto; restore só com autorização + backup SHA |
| CORS incorreto | Bloco 2 seta domínio oficial único |

---

## 4. Rollback (resumo)

1. **Padrão:** Bloco 7 — checkout do `OLD_HEAD` (pré-deploy), preservar `database/` + `.env`, restart, health.  
2. **Config:** restaurar `$CFG_BAK/.env` do Bloco 2 se a config tiver sido o problema.  
3. **Banco:** **nunca** automático; só com evidência de corrupção + autorização humana + SHA do backup FIT-06.

Ver também: `FIT06_ROLLBACK_PLAN.md`.

---

## 5. Confirmação de não-execução

- Nenhum comando SSH foi executado neste pacote FIT-08.  
- Nenhum acesso VPS.  
- Nenhum restart.  
- Nenhum alter do banco.  
- Nenhuma migration.  
- Nenhum deploy automático.  
- `main` permanece no merge commit documentado; este arquivo é **plano**.  
