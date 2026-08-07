#!/usr/bin/env bash
# FIT08-B6-R2 — SMOKE TEST DE PRODUÇÃO (somente leitura)
# Contrato de páginas alinhado às rotas reais em backend/main.py.
# Não usa set -e: acumula falhas e executa todas as verificações.
set +e
set -u
set -o pipefail

APP=/var/www/absenteismo
TARGET_HEAD=540cda0806326aa14ced57d42fd43e8a69817d08
BASE=http://127.0.0.1:8000
HTTPS_BASE=https://www.absenteismocontroller.com.br
OFFICIAL_ORIGIN=https://www.absenteismocontroller.com.br
RANDOM_ORIGIN=https://evil-example-$(date +%s).invalid
DB="$APP/database/absenteismo.db"
SERVICE=absenteismocontroller.service
PY=/var/www/absenteismo/venv/bin/python3
SMOKE_ID=FIT08-B6-R2

HEAD=""
SERVICE_STATUS=""
PORT_8000=no
HEALTH_HTTP=""
HEALTH_STATUS=""
DATABASE_HEALTHY=no
DATABASE_INTEGRITY=no
PUBLIC_ROUTES_OK=no
PROTECTED_ROUTES_OK=no
EXPERIMENTAL_ROUTES_OFF=no
API_DOCS_OFF=no
SECURITY_HEADERS_OK=no
CORS_OK=no
CLIENT_2_OK=no
CLIENT_4_OK=no
USERS_OK=no
COMMON_PASSWORDS_ZERO=no
DB_PRESERVED=no
SMOKE_RESULT=NO_GO
FAILS=0
NOTES=()

note() { NOTES+=("$*"); echo "NOTE: $*"; }
fail_item() { FAILS=$((FAILS + 1)); echo "FAIL_ITEM: $*"; }

print_summary() {
  echo "======== RESUMO ${SMOKE_ID} ========"
  echo "HEAD=${HEAD:-}"
  echo "SERVICE_STATUS=${SERVICE_STATUS:-}"
  echo "PORT_8000=${PORT_8000:-no}"
  echo "HEALTH_HTTP=${HEALTH_HTTP:-}"
  echo "HEALTH_STATUS=${HEALTH_STATUS:-}"
  echo "DATABASE_HEALTHY=${DATABASE_HEALTHY:-no}"
  echo "DATABASE_INTEGRITY=${DATABASE_INTEGRITY:-no}"
  echo "PUBLIC_ROUTES_OK=${PUBLIC_ROUTES_OK:-no}"
  echo "PROTECTED_ROUTES_OK=${PROTECTED_ROUTES_OK:-no}"
  echo "EXPERIMENTAL_ROUTES_OFF=${EXPERIMENTAL_ROUTES_OFF:-no}"
  echo "API_DOCS_OFF=${API_DOCS_OFF:-no}"
  echo "SECURITY_HEADERS_OK=${SECURITY_HEADERS_OK:-no}"
  echo "CORS_OK=${CORS_OK:-no}"
  echo "CLIENT_2_OK=${CLIENT_2_OK:-no}"
  echo "CLIENT_4_OK=${CLIENT_4_OK:-no}"
  echo "USERS_OK=${USERS_OK:-no}"
  echo "COMMON_PASSWORDS_ZERO=${COMMON_PASSWORDS_ZERO:-no}"
  echo "DB_PRESERVED=${DB_PRESERVED:-no}"
  echo "SMOKE_RESULT=${SMOKE_RESULT:-NO_GO}"
  echo "FAIL_COUNT=$FAILS"
  if [ "${#NOTES[@]}" -gt 0 ]; then
    echo "--- NOTES ---"
    printf '%s\n' "${NOTES[@]}"
  fi
}

http_code() {
  local method=${1:-GET}
  local url=$2
  shift 2 || true
  curl -sS -o /dev/null -w '%{http_code}' -m 12 -X "$method" "$url" "$@" 2>/dev/null || echo ERR
}

echo "=== ${SMOKE_ID} — SMOKE PRODUÇÃO (READ ONLY) ==="
echo "ROUTE_MAP (backend/main.py):"
echo "  home/dashboard -> /  (index.html)  [alias /index.html]"
echo "  login          -> /login"
echo "  clientes       -> /clientes"
echo "  funcionarios   -> /funcionarios"
echo "  upload         -> /upload"
echo "  produtividade  -> /produtividade"
echo "  dados Power BI -> /dados_powerbi  (frontend/dados_powerbi.html)"
echo "  dashboard_powerbi.html -> /dashboard_powerbi"
echo "  NAO_REGISTRADA: /dashboard , /dados-powerbi"

if [ ! -d "$APP" ]; then fail_item "APP ausente"; print_summary; exit 1; fi
cd "$APP" || { fail_item "cd APP falhou"; print_summary; exit 1; }
if [ ! -x "$PY" ]; then fail_item "python venv ausente"; print_summary; exit 1; fi
if [ ! -f "$DB" ]; then fail_item "banco ausente"; print_summary; exit 1; fi

HEAD=$(git rev-parse HEAD 2>/dev/null || echo UNKNOWN)
echo "HEAD=$HEAD"
[ "$HEAD" = "$TARGET_HEAD" ] || fail_item "HEAD != TARGET ($TARGET_HEAD)"

SERVICE_STATUS=$(systemctl is-active "$SERVICE" 2>/dev/null || echo inactive)
echo "SERVICE_STATUS=$SERVICE_STATUS"
[ "$SERVICE_STATUS" = "active" ] || fail_item "serviço não active"

PORT_8000=no
if ss -ltn 2>/dev/null | grep -qE '127\.0\.0\.1:8000([[:space:]]|$)'; then
  PORT_8000=yes
else
  PORT_8000=$("$PY" - <<'PY'
import socket
s=socket.socket(); s.settimeout(1)
try:
    s.connect(("127.0.0.1", 8000)); print("yes")
except Exception:
    print("no")
finally:
    s.close()
PY
)
fi
echo "PORT_8000=$PORT_8000"
[ "$PORT_8000" = "yes" ] || fail_item "porta 8000 não escuta"

DB_META_BEFORE=$("$PY" - <<PY
import os, hashlib
p = "$DB"
h = hashlib.sha256()
with open(p, "rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        h.update(chunk)
print(h.hexdigest())
print(os.path.getsize(p))
PY
)
DB_SHA_BEFORE=$(echo "$DB_META_BEFORE" | sed -n '1p')
DB_SIZE_BEFORE=$(echo "$DB_META_BEFORE" | sed -n '2p')
echo "DB_SHA_BEFORE=$DB_SHA_BEFORE"
echo "DB_SIZE_BEFORE=$DB_SIZE_BEFORE"

# --- health ---
HEALTH_TMP=$(mktemp)
HEALTH_HTTP=$(curl -sS -m 12 -o "$HEALTH_TMP" -w '%{http_code}' "$BASE/api/health" 2>/dev/null || echo ERR)
echo "HEALTH_HTTP=$HEALTH_HTTP"
if [ "$HEALTH_HTTP" = "200" ]; then
  HEALTH_STATUS=$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8")).get("status",""))' "$HEALTH_TMP")
  DATABASE_HEALTHY=$("$PY" -c 'import json,sys; d=json.load(open(sys.argv[1],encoding="utf-8")); print("yes" if (d.get("checks") or {}).get("database",{}).get("healthy") is True else "no")' "$HEALTH_TMP")
  DATABASE_INTEGRITY=$("$PY" -c 'import json,sys; db=(json.load(open(sys.argv[1],encoding="utf-8")).get("checks") or {}).get("database") or {}; print("yes" if (db.get("integrity_ok") is True or db.get("integrity_check") is True) else "no")' "$HEALTH_TMP")
else
  HEALTH_STATUS=FAIL
  DATABASE_HEALTHY=no
  DATABASE_INTEGRITY=no
  fail_item "GET /api/health != 200"
fi
rm -f "$HEALTH_TMP"
echo "HEALTH_STATUS=$HEALTH_STATUS"
echo "DATABASE_HEALTHY=$DATABASE_HEALTHY"
echo "DATABASE_INTEGRITY=$DATABASE_INTEGRITY"
[ "$HEALTH_STATUS" = "ok" ] || fail_item "health status != ok"
[ "$DATABASE_HEALTHY" = "yes" ] || fail_item "database.healthy != true"
[ "$DATABASE_INTEGRITY" = "yes" ] || fail_item "database integrity flag != true"

# --- páginas reais ---
echo "--- páginas reais ---"
PAGE_FAILS_BEFORE=$FAILS
check_page() {
  local label=$1 path=$2
  local code loc
  code=$(curl -sS -o /dev/null -w '%{http_code}' -m 12 "$BASE$path" 2>/dev/null || echo ERR)
  loc=$(curl -sS -o /dev/null -D - -m 12 "$BASE$path" 2>/dev/null | tr -d '\r' | awk 'tolower($1)=="location:"{print $2; exit}')
  echo "PAGE [$label] $path -> $code loc=${loc:-}"
  case "$code" in
    200) return 0 ;;
    301|302|303|307|308)
      case "$(printf '%s' "${loc:-}" | tr '[:upper:]' '[:lower:]')" in
        *login*) return 0 ;;
        *) fail_item "redirect sem login em $path"; return 1 ;;
      esac
      ;;
    *) fail_item "página $path code=$code"; return 1 ;;
  esac
}

# Rotas fictícias do contrato antigo — não falham o smoke
for bogus in /dashboard /dados-powerbi; do
  code=$(http_code GET "$BASE$bogus")
  echo "PAGE [NAO_REGISTRADA] $bogus -> $code"
  note "NAO_REGISTRADA $bogus (não faz parte do contrato FastAPI atual)"
done

check_page "home/dashboard" "/"
check_page "home_alias" "/index.html"
check_page "login" "/login"
check_page "clientes" "/clientes"
check_page "funcionarios" "/funcionarios"
check_page "upload" "/upload"
check_page "produtividade" "/produtividade"
check_page "dados_powerbi" "/dados_powerbi"
check_page "dashboard_powerbi" "/dashboard_powerbi"

if [ "$FAILS" -eq "$PAGE_FAILS_BEFORE" ]; then
  PUBLIC_ROUTES_OK=yes
else
  PUBLIC_ROUTES_OK=no
fi

# --- APIs públicas ---
echo "--- APIs públicas ---"
hcode=$(http_code GET "$BASE/api/health")
[ "$hcode" = "200" ] || fail_item "health público falhou ($hcode)"
lcode=$(curl -sS -o /dev/null -w '%{http_code}' -m 12 -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data 'username=smoke-invalid&password=smoke-invalid' 2>/dev/null || echo ERR)
echo "LOGIN_PROBE=$lcode"
case "$lcode" in 401|422|400) ;; *) fail_item "login probe inesperado ($lcode)" ;; esac

# --- APIs protegidas sem token (rotas API reais) ---
echo "--- APIs protegidas sem token ---"
prot_fail=0
for path in /api/clientes /api/uploads /api/users /api/dashboard /api/auth/me /api/dados/todos; do
  code=$(http_code GET "$BASE$path")
  echo "ANON $path -> $code"
  case "$code" in
    401|403) ;;
    200|500|ERR)
      echo "FAIL_ITEM: $path=$code"; prot_fail=$((prot_fail + 1))
      ;;
    404) note "API $path retornou 404" ;;
    *) echo "FAIL_ITEM: $path=$code"; prot_fail=$((prot_fail + 1)) ;;
  esac
done
if [ "$prot_fail" -eq 0 ]; then PROTECTED_ROUTES_OK=yes; else PROTECTED_ROUTES_OK=no; FAILS=$((FAILS + prot_fail)); fi

# --- experimentais / docs ---
echo "--- experimentais + docs ---"
exp_fail=0
docs_fail=0
for path in /api/ingestion /api/ingestion/preview /api/ingestion/import /experimental/ingestion /api/performance /api/performance/shadow; do
  code=$(http_code GET "$BASE$path")
  echo "EXP $path -> $code"
  case "$code" in
    404|401|403|405) ;;
    200|500) echo "FAIL_ITEM: experimental exposta $path=$code"; exp_fail=$((exp_fail + 1)) ;;
    *) ;;
  esac
done
for path in /docs /redoc /openapi.json; do
  code=$(http_code GET "$BASE$path")
  echo "DOCS $path -> $code"
  case "$code" in
    404|401|403) ;;
    200) echo "FAIL_ITEM: docs expostos $path"; docs_fail=$((docs_fail + 1)) ;;
    *) ;;
  esac
done
if [ "$exp_fail" -eq 0 ]; then EXPERIMENTAL_ROUTES_OFF=yes; else EXPERIMENTAL_ROUTES_OFF=no; FAILS=$((FAILS + exp_fail)); fi
if [ "$docs_fail" -eq 0 ]; then API_DOCS_OFF=yes; else API_DOCS_OFF=no; FAILS=$((FAILS + docs_fail)); fi

# --- security headers ---
echo "--- security headers ---"
HDRS=$(curl -sS -D - -o /dev/null -m 12 "$BASE/api/health" 2>/dev/null | tr -d '\r')
hdr_fail=0
for h in content-security-policy x-frame-options x-content-type-options referrer-policy permissions-policy; do
  if echo "$HDRS" | grep -Eiq "^${h}:"; then
    echo "HDR_OK $h"
  else
    echo "HDR_MISS $h"; hdr_fail=$((hdr_fail + 1))
  fi
done
CC=$(echo "$HDRS" | awk 'tolower($1)=="cache-control:"{print tolower($0)}')
echo "CACHE_CONTROL_LINE=$CC"
echo "$CC" | grep -Eq 'no-store|no-cache|private' || { echo "FAIL_ITEM: cache-control sensível ausente"; hdr_fail=$((hdr_fail + 1)); }

HSTS_LINE=$(curl -sS -D - -o /dev/null -m 15 "$HTTPS_BASE/api/health" 2>/dev/null | tr -d '\r' | awk 'tolower($1)=="strict-transport-security:"{print; exit}')
echo "HSTS_LINE=${HSTS_LINE:-ABSENT_OR_HTTPS_UNREACHABLE}"
if [ -n "${HSTS_LINE:-}" ]; then
  echo "HDR_OK strict-transport-security"
else
  echo "FAIL_ITEM: Strict-Transport-Security ausente no domínio HTTPS"
  hdr_fail=$((hdr_fail + 1))
fi
if [ "$hdr_fail" -eq 0 ]; then SECURITY_HEADERS_OK=yes; else SECURITY_HEADERS_OK=no; FAILS=$((FAILS + hdr_fail)); fi

# --- CORS ---
echo "--- CORS ---"
CORS_OK_OFFICIAL=$(curl -sS -D - -o /dev/null -m 12 -X OPTIONS "$BASE/api/health" \
  -H "Origin: $OFFICIAL_ORIGIN" \
  -H "Access-Control-Request-Method: GET" 2>/dev/null | tr -d '\r' | awk 'tolower($1)=="access-control-allow-origin:"{print $2; exit}')
CORS_BAD=$(curl -sS -D - -o /dev/null -m 12 -X OPTIONS "$BASE/api/health" \
  -H "Origin: $RANDOM_ORIGIN" \
  -H "Access-Control-Request-Method: GET" 2>/dev/null | tr -d '\r' | awk 'tolower($1)=="access-control-allow-origin:"{print $2; exit}')
echo "CORS_OFFICIAL=${CORS_OK_OFFICIAL:-ABSENT}"
echo "CORS_RANDOM=${CORS_BAD:-ABSENT}"
cors_fail=0
[ "${CORS_OK_OFFICIAL:-}" = "$OFFICIAL_ORIGIN" ] || { fail_item "CORS oficial não refletido"; cors_fail=1; }
if [ -n "${CORS_BAD:-}" ]; then fail_item "CORS permitiu origem aleatória"; cors_fail=1; fi
if [ "$cors_fail" -eq 0 ]; then CORS_OK=yes; else CORS_OK=no; fi

# --- banco via Python sqlite3 (readonly URI) ---
echo "--- inventário agregado (Python sqlite3, mode=ro) ---"
INV=$("$PY" - <<PY
import sqlite3
db = "$DB"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
cur = con.cursor()
qc = cur.execute("PRAGMA quick_check").fetchone()[0]
ic = cur.execute("PRAGMA integrity_check").fetchone()[0]
c2 = cur.execute("SELECT COUNT(*) FROM clients WHERE id=2").fetchone()[0]
c4 = cur.execute("SELECT COUNT(*) FROM clients WHERE id=4").fetchone()[0]
u2 = cur.execute("SELECT COUNT(*) FROM uploads WHERE client_id=2").fetchone()[0]
u4 = cur.execute("SELECT COUNT(*) FROM uploads WHERE client_id=4").fetchone()[0]
e2 = cur.execute("SELECT COUNT(*) FROM atestados WHERE client_id=2").fetchone()[0]
e4 = cur.execute("SELECT COUNT(*) FROM atestados WHERE client_id=4").fetchone()[0]
users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
admins = cur.execute(
    "SELECT COUNT(*) FROM users WHERE IFNULL(is_admin,0)=1 AND IFNULL(is_active,0)=1"
).fetchone()[0]
orphan = cur.execute(
    "SELECT COUNT(*) FROM users WHERE IFNULL(is_admin,0)=0 AND client_id IS NULL"
).fetchone()[0]
con.close()
print(f"QC={qc}")
print(f"IC={ic}")
print(f"C2={c2}")
print(f"C4={c4}")
print(f"U2={u2}")
print(f"U4={u4}")
print(f"E2={e2}")
print(f"E4={e4}")
print(f"USERS={users}")
print(f"ADMINS={admins}")
print(f"ORPHAN={orphan}")
PY
)
echo "$INV"
QC=$(echo "$INV" | awk -F= '/^QC=/{print $2}')
IC=$(echo "$INV" | awk -F= '/^IC=/{print $2}')
C2=$(echo "$INV" | awk -F= '/^C2=/{print $2}')
C4=$(echo "$INV" | awk -F= '/^C4=/{print $2}')
U2=$(echo "$INV" | awk -F= '/^U2=/{print $2}')
U4=$(echo "$INV" | awk -F= '/^U4=/{print $2}')
E2=$(echo "$INV" | awk -F= '/^E2=/{print $2}')
E4=$(echo "$INV" | awk -F= '/^E4=/{print $2}')
USERS_TOTAL=$(echo "$INV" | awk -F= '/^USERS=/{print $2}')
ADMINS_ACTIVE=$(echo "$INV" | awk -F= '/^ADMINS=/{print $2}')
ORPHAN_NON_ADMIN=$(echo "$INV" | awk -F= '/^ORPHAN=/{print $2}')

[ "$QC" = "ok" ] || fail_item "quick_check != ok"
[ "$IC" = "ok" ] || fail_item "integrity_check != ok"

echo "CLIENT_2_PRESENT=$C2 UPLOADS=$U2 EVENTS=$E2"
echo "CLIENT_4_PRESENT=$C4 UPLOADS=$U4 EVENTS=$E4"
echo "USERS_TOTAL=$USERS_TOTAL ADMINS_ACTIVE=$ADMINS_ACTIVE ORPHAN_NON_ADMIN=$ORPHAN_NON_ADMIN"

if [ "$C2" = "1" ] && [ "$U2" = "18" ] && [ "$E2" = "4520" ]; then CLIENT_2_OK=yes; else fail_item "contagens client 2 divergem"; CLIENT_2_OK=no; fi
if [ "$C4" = "1" ] && [ "$U4" = "14" ] && [ "$E4" = "333" ]; then CLIENT_4_OK=yes; else fail_item "contagens client 4 divergem"; CLIENT_4_OK=no; fi
if [ "$USERS_TOTAL" = "3" ] && [ "$ADMINS_ACTIVE" = "2" ] && [ "$ORPHAN_NON_ADMIN" = "0" ]; then USERS_OK=yes; else fail_item "contagens de usuários divergem"; USERS_OK=no; fi

echo "--- common password count (sem usernames/hashes) ---"
COMMON_COUNT=$("$PY" - <<PY
import sqlite3
import bcrypt
db = "$DB"
commons = [
    b"admin123", b"admin", b"123456", b"password", b"senha", b"senha123",
    b"12345678", b"admin@123", b"Admin123", b"changeme", b"qwerty",
]
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("SELECT password_hash FROM users").fetchall()
con.close()
hits = 0
for (h,) in rows:
    if not h:
        continue
    hb = h.encode("utf-8") if isinstance(h, str) else h
    for p in commons:
        try:
            if bcrypt.checkpw(p, hb):
                hits += 1
                break
        except Exception:
            continue
print(hits)
PY
)
echo "COMMON_PASSWORD_HITS=$COMMON_COUNT"
if [ "$COMMON_COUNT" = "0" ]; then COMMON_PASSWORDS_ZERO=yes; else fail_item "contas com senha comum > 0"; COMMON_PASSWORDS_ZERO=no; fi

DB_META_AFTER=$("$PY" - <<PY
import os, hashlib
p = "$DB"
h = hashlib.sha256()
with open(p, "rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        h.update(chunk)
print(h.hexdigest())
print(os.path.getsize(p))
PY
)
DB_SHA_AFTER=$(echo "$DB_META_AFTER" | sed -n '1p')
DB_SIZE_AFTER=$(echo "$DB_META_AFTER" | sed -n '2p')
echo "DB_SHA_AFTER=$DB_SHA_AFTER"
echo "DB_SIZE_AFTER=$DB_SIZE_AFTER"
if [ "$DB_SHA_AFTER" = "$DB_SHA_BEFORE" ] && [ "$DB_SIZE_AFTER" = "$DB_SIZE_BEFORE" ]; then
  DB_PRESERVED=yes
else
  DB_PRESERVED=no
  fail_item "banco alterado durante smoke"
fi

if [ "$FAILS" -eq 0 ]; then SMOKE_RESULT=GO; else SMOKE_RESULT=NO_GO; fi
print_summary
[ "$SMOKE_RESULT" = "GO" ]
exit $?
