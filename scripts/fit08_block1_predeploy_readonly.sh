#!/usr/bin/env bash
# FIT-08 BLOCO 1 — PRÉ-DEPLOY SOMENTE LEITURA (não altera nada)
set +e
APP=/var/www/absenteismo
TARGET=540cda0806326aa14ced57d42fd43e8a69817d08
BACKUP=/root/backups/absenteismo/absenteismo_pre_fit06_20260807_000226.db
EXPECT_BACKUP_SHA=13c485ace101695b792ac1dd9f634cd9291ccc381b33dbaeb79f3f316acae1ff
DB="$APP/database/absenteismo.db"
ENVF="$APP/.env"

PREDEPLOY_RESULT=GO
fail() { PREDEPLOY_RESULT=NO_GO; echo "FAIL: $*"; }

echo "=== FIT-08 BLOCO 1 — READ ONLY ==="
cd "$APP" || { fail "cd $APP"; }

echo "pwd=$(pwd)"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo UNKNOWN)
OLD_HEAD=$(git rev-parse HEAD 2>/dev/null || echo UNKNOWN)
echo "CURRENT_BRANCH=$CURRENT_BRANCH"
echo "OLD_HEAD=$OLD_HEAD"
[ "$OLD_HEAD" != "UNKNOWN" ] && [ -n "$OLD_HEAD" ] || fail "HEAD inválido"

echo "--- git status --short ---"
git status --short
TRACKED_DIRTY=no
if git status --porcelain 2>/dev/null | grep -E '^[MADRCUT ]{1,2}' | grep -vqE '^\?\?'; then
  TRACKED_DIRTY=yes
  fail "há alterações tracked"
fi
# também marca dirty se houver M/A/D na primeira coluna
if git status --porcelain 2>/dev/null | grep -qE '^[MADRCU]|^[ M][MD]'; then
  TRACKED_DIRTY=yes
  fail "working tree tracked dirty"
fi

echo "--- origin/main (somente leitura via ls-remote; sem pull/fetch) ---"
ORIGIN_MAIN=$(git ls-remote origin refs/heads/main 2>/dev/null | awk '{print $1}')
echo "ORIGIN_MAIN=$ORIGIN_MAIN"
[ -n "$ORIGIN_MAIN" ] || fail "origin/main inacessível"
[ "$ORIGIN_MAIN" = "$TARGET" ] || fail "origin/main != TARGET $TARGET"

echo "--- serviço ---"
SERVICE_STATUS=$(systemctl is-active absenteismocontroller.service 2>/dev/null || echo inactive)
echo "SERVICE_STATUS=$SERVICE_STATUS"
systemctl status absenteismocontroller.service --no-pager -n 15 2>/dev/null | sed -n '1,20p'
[ "$SERVICE_STATUS" = "active" ] || fail "serviço não está active"

echo "--- health ---"
HEALTH_STATUS=$(curl -sS -m 5 http://127.0.0.1:8000/api/health 2>/dev/null || echo FAIL)
echo "HEALTH_STATUS=$HEALTH_STATUS"
echo "$HEALTH_STATUS" | grep -Eqi 'ok|healthy|true|"status"' || fail "health inválido"

echo "--- banco vivo ---"
if [ -f "$DB" ]; then
  LIVE_DB=yes
  ls -lh "$DB"
  du -h "$DB" | awk '{print "LIVE_DB_SIZE="$1}'
else
  LIVE_DB=no
  fail "banco vivo ausente: $DB"
fi

echo "--- backup FIT-06 ---"
BACKUP_SHA_OK=no
if [ -f "$BACKUP" ]; then
  BACKUP_SHA=$(sha256sum "$BACKUP" | awk '{print $1}')
  echo "BACKUP_PATH=$BACKUP"
  echo "BACKUP_SHA=$BACKUP_SHA"
  ls -lh "$BACKUP"
  if [ "$BACKUP_SHA" = "$EXPECT_BACKUP_SHA" ]; then
    BACKUP_SHA_OK=yes
  else
    fail "SHA do backup diverge"
  fi
else
  fail "backup ausente: $BACKUP"
fi

echo "--- .env presença (SECRET_KEY mascarada) ---"
SECRET_KEY_PRESENT=no
FLAGS_SAFE=no
ENV_OK=yes
if [ ! -f "$ENVF" ]; then
  ENV_OK=no
  fail ".env ausente"
else
  get_env() {
    grep -E "^[[:space:]]*${1}=" "$ENVF" 2>/dev/null | tail -1 | sed -E "s/^[[:space:]]*${1}=//"
  }
  ENV_VAL=$(get_env ENVIRONMENT)
  ING_VAL=$(get_env ENABLE_INTELLIGENT_INGESTION)
  PERF_VAL=$(get_env ENABLE_BIOMED_PERFORMANCE_ENGINE)
  DOCS_VAL=$(get_env ENABLE_API_DOCS)
  CORS_VAL=$(get_env CORS_ALLOWED_ORIGINS)
  SK_VAL=$(get_env SECRET_KEY)

  echo "ENVIRONMENT=${ENV_VAL:-ABSENT}"
  echo "ENABLE_INTELLIGENT_INGESTION=${ING_VAL:-ABSENT}"
  echo "ENABLE_BIOMED_PERFORMANCE_ENGINE=${PERF_VAL:-ABSENT}"
  echo "ENABLE_API_DOCS=${DOCS_VAL:-ABSENT}"
  echo "CORS_ALLOWED_ORIGINS=${CORS_VAL:-ABSENT}"
  if [ -n "${SK_VAL:-}" ]; then
    SECRET_KEY_PRESENT=yes
    echo "SECRET_KEY=PRESENT"
  else
    echo "SECRET_KEY=ABSENT"
    fail "SECRET_KEY ausente"
  fi

  norm() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]'; }
  N_ENV=$(norm "${ENV_VAL:-}")
  N_ING=$(norm "${ING_VAL:-false}")
  N_PERF=$(norm "${PERF_VAL:-false}")
  N_DOCS=$(norm "${DOCS_VAL:-false}")
  echo "FLAGS_NORMALIZED: ENVIRONMENT=$N_ENV INGESTION=$N_ING PERFORMANCE=$N_PERF API_DOCS=$N_DOCS"
  if [ "$N_ENV" = "production" ] && \
     { [ "$N_ING" = "false" ] || [ "$N_ING" = "0" ] || [ -z "$N_ING" ]; } && \
     { [ "$N_PERF" = "false" ] || [ "$N_PERF" = "0" ] || [ -z "$N_PERF" ]; } && \
     { [ "$N_DOCS" = "false" ] || [ "$N_DOCS" = "0" ] || [ -z "$N_DOCS" ]; }; then
    FLAGS_SAFE=yes
  else
    fail "flags/ENVIRONMENT inseguros"
  fi
fi

echo "--- untracked críticos ---"
UNTRACKED_OK=yes
for f in database/ .env gunicorn_config.py logs/ nohup.out; do
  if [ -e "$APP/$f" ]; then
    echo "PRESERVE_OK $f"
  else
    echo "MISSING $f"
    UNTRACKED_OK=no
    fail "faltando $f"
  fi
done

echo "--- disco ---"
df -h "$APP" /root 2>/dev/null || df -h
echo "--- memória ---"
free -h 2>/dev/null || cat /proc/meminfo | head -5

[ "$PREDEPLOY_RESULT" = "GO" ] || PREDEPLOY_RESULT=NO_GO

echo "======== RESUMO ========"
echo "OLD_HEAD=$OLD_HEAD"
echo "CURRENT_BRANCH=$CURRENT_BRANCH"
echo "ORIGIN_MAIN=$ORIGIN_MAIN"
echo "SERVICE_STATUS=$SERVICE_STATUS"
echo "HEALTH_STATUS=$HEALTH_STATUS"
echo "LIVE_DB=$LIVE_DB"
echo "BACKUP_SHA_OK=$BACKUP_SHA_OK"
echo "SECRET_KEY_PRESENT=$SECRET_KEY_PRESENT"
echo "FLAGS_SAFE=$FLAGS_SAFE"
echo "TRACKED_DIRTY=$TRACKED_DIRTY"
echo "PREDEPLOY_RESULT=$PREDEPLOY_RESULT"
