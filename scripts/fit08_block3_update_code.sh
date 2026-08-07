#!/usr/bin/env bash
# FIT-08 BLOCO 3 — ATUALIZAÇÃO CONTROLADA DO CÓDIGO
# Fast-forward only até TARGET. Sem reset/clean/pip/restart/migration/.env/db writes.
# Sem rollback automático em caso de NO_GO.
set -euo pipefail

APP=/var/www/absenteismo
EXPECTED_OLD_HEAD=d0c012abaae9191531c3d2f30cb909407d31af01
TARGET_HEAD=540cda0806326aa14ced57d42fd43e8a69817d08
DB="$APP/database/absenteismo.db"
ENVF="$APP/.env"
GUNI="$APP/gunicorn_config.py"

OLD_HEAD=""
DEPLOYED_HEAD=""
DB_SHA_BEFORE=""
DB_SHA_AFTER=""
DB_SIZE_BEFORE=""
DB_SIZE_AFTER=""
ENV_SHA_BEFORE=""
ENV_SHA_AFTER=""
GUNICORN_SHA_BEFORE=""
GUNICORN_SHA_AFTER=""
FAST_FORWARD_OK=no
DB_PRESERVED=no
ENV_PRESERVED=no
GUNICORN_PRESERVED=no
UNTRACKED_PRESERVED=no
CODE_UPDATE_RESULT=NO_GO
MERGE_DONE=no

print_summary() {
  echo "======== RESUMO ========"
  echo "OLD_HEAD=${OLD_HEAD:-}"
  echo "TARGET_HEAD=${TARGET_HEAD}"
  echo "DEPLOYED_HEAD=${DEPLOYED_HEAD:-}"
  echo "FAST_FORWARD_OK=${FAST_FORWARD_OK:-no}"
  echo "DB_PRESERVED=${DB_PRESERVED:-no}"
  echo "ENV_PRESERVED=${ENV_PRESERVED:-no}"
  echo "GUNICORN_PRESERVED=${GUNICORN_PRESERVED:-no}"
  echo "UNTRACKED_PRESERVED=${UNTRACKED_PRESERVED:-no}"
  echo "CODE_UPDATE_RESULT=${CODE_UPDATE_RESULT:-NO_GO}"
}

fail() {
  echo "FAIL: $*" >&2
  CODE_UPDATE_RESULT=NO_GO
  # Captura HEAD atual se já existir checkout
  DEPLOYED_HEAD=$(git -C "$APP" rev-parse HEAD 2>/dev/null || echo "${DEPLOYED_HEAD:-}")
  print_summary
  if [ "$MERGE_DONE" = "yes" ]; then
    echo "NOTE: merge já ocorreu; rollback automático NÃO será feito (política FIT-08)." >&2
  else
    echo "NOTE: merge NÃO foi executado." >&2
  fi
  exit 1
}

sha_file() { sha256sum "$1" | awk '{print $1}'; }
size_file() { stat -c '%s' "$1"; }

echo "=== FIT-08 BLOCO 3 — ATUALIZAÇÃO CONTROLADA DO CÓDIGO ==="

[ -d "$APP" ] || fail "APP ausente: $APP"
cd "$APP"

# 2–3 branch / APP
[ "$(pwd)" = "$APP" ] || fail "pwd != APP"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "CURRENT_BRANCH=$CURRENT_BRANCH"
[ "$CURRENT_BRANCH" = "main" ] || fail "branch atual != main"

# 4 HEAD atual exatamente OLD esperado
OLD_HEAD=$(git rev-parse HEAD)
echo "OLD_HEAD=$OLD_HEAD"
[ "$OLD_HEAD" = "$EXPECTED_OLD_HEAD" ] || fail "HEAD atual != EXPECTED_OLD_HEAD ($EXPECTED_OLD_HEAD)"

# 5 ausência de alterações tracked
echo "--- git status --short ---"
git status --short
if git status --porcelain | grep -qE '^[MADRCU]|^.[MADRCU]'; then
  fail "há alterações tracked na working tree"
fi
# ignora ?? untracked; qualquer outra marca é dirty
if git status --porcelain | grep -vE '^\?\?' | grep -q .; then
  fail "working tree tracked dirty"
fi

# 6 untracked críticos
echo "--- untracked críticos (pré) ---"
for f in database/ .env gunicorn_config.py logs/ nohup.out; do
  if [ -e "$APP/$f" ]; then
    echo "PRESERVE_OK $f"
  else
    fail "faltando artefato crítico: $f"
  fi
done
[ -f "$DB" ] || fail "banco vivo ausente: $DB"
[ -f "$ENVF" ] || fail ".env ausente"
[ -f "$GUNI" ] || fail "gunicorn_config.py ausente"

DB_SHA_BEFORE=$(sha_file "$DB")
DB_SIZE_BEFORE=$(size_file "$DB")
ENV_SHA_BEFORE=$(sha_file "$ENVF")
GUNICORN_SHA_BEFORE=$(sha_file "$GUNI")

echo "DB_SHA_BEFORE=$DB_SHA_BEFORE"
echo "DB_SIZE_BEFORE=$DB_SIZE_BEFORE"
echo "ENV_SHA_BEFORE=$ENV_SHA_BEFORE"
echo "GUNICORN_SHA_BEFORE=$GUNICORN_SHA_BEFORE"

# 7 fetch
git fetch origin main

# 8 origin/main == TARGET
REMOTE_MAIN=$(git rev-parse origin/main)
echo "origin/main=$REMOTE_MAIN"
[ "$REMOTE_MAIN" = "$TARGET_HEAD" ] || fail "origin/main != TARGET_HEAD"

# 9 OLD é ancestral de TARGET
if ! git merge-base --is-ancestor "$OLD_HEAD" "$TARGET_HEAD"; then
  fail "OLD_HEAD não é ancestral de TARGET_HEAD (FF impossível)"
fi

# 10 fast-forward only
echo "--- git merge --ff-only origin/main ---"
git merge --ff-only origin/main
MERGE_DONE=yes
FAST_FORWARD_OK=yes

# 11 HEAD final
DEPLOYED_HEAD=$(git rev-parse HEAD)
echo "DEPLOYED_HEAD=$DEPLOYED_HEAD"
[ "$DEPLOYED_HEAD" = "$TARGET_HEAD" ] || fail "HEAD final != TARGET_HEAD"

# 12 untracked ainda existem
echo "--- untracked críticos (pós) ---"
UNTRACKED_PRESERVED=yes
for f in database/ .env gunicorn_config.py logs/ nohup.out; do
  if [ -e "$APP/$f" ]; then
    echo "PRESERVE_OK $f"
  else
    UNTRACKED_PRESERVED=no
    fail "artefato crítico ausente após merge: $f"
  fi
done

# 13 banco mesmo tamanho e SHA; .env e gunicorn intactos
DB_SHA_AFTER=$(sha_file "$DB")
DB_SIZE_AFTER=$(size_file "$DB")
ENV_SHA_AFTER=$(sha_file "$ENVF")
GUNICORN_SHA_AFTER=$(sha_file "$GUNI")

echo "DB_SHA_AFTER=$DB_SHA_AFTER"
echo "DB_SIZE_AFTER=$DB_SIZE_AFTER"
echo "ENV_SHA_AFTER=$ENV_SHA_AFTER"
echo "GUNICORN_SHA_AFTER=$GUNICORN_SHA_AFTER"

[ "$DB_SHA_BEFORE" = "$DB_SHA_AFTER" ] && [ "$DB_SIZE_BEFORE" = "$DB_SIZE_AFTER" ] || {
  DB_PRESERVED=no
  fail "banco alterado (SHA/tamanho diverge) — não deveria ter sido tocado"
}
DB_PRESERVED=yes

[ "$ENV_SHA_BEFORE" = "$ENV_SHA_AFTER" ] || {
  ENV_PRESERVED=no
  fail ".env alterado durante atualização de código"
}
ENV_PRESERVED=yes

[ "$GUNICORN_SHA_BEFORE" = "$GUNICORN_SHA_AFTER" ] || {
  GUNICORN_PRESERVED=no
  fail "gunicorn_config.py alterado durante atualização de código"
}
GUNICORN_PRESERVED=yes

# Garantia final: sem reset/clean usados; tree tracked limpa
if git status --porcelain | grep -vE '^\?\?' | grep -q .; then
  fail "tracked dirty após merge"
fi

CODE_UPDATE_RESULT=GO
print_summary
