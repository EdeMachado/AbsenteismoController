#!/usr/bin/env bash
# FIT-08 BLOCO 2 — PREPARAR CONFIGURAÇÃO
# Idempotente. Não faz git/pip/restart/deploy/migration/alteração de banco.
# Em falha de validação: restaura apenas .env a partir do backup deste bloco.
set -euo pipefail

APP=/var/www/absenteismo
ENVF="$APP/.env"
GUNI="$APP/gunicorn_config.py"
TS=$(date -u +%Y%m%d_%H%M%S)
CONFIG_BACKUP_DIR="/root/backups/absenteismo/config_pre_fit08_${TS}"
ENV_BACKUP=""
GUNICORN_BACKUP=""
ENV_SHA_BEFORE=""
ENV_SHA_AFTER=""
SECRET_KEY_PRESERVED=no
FLAGS_SAFE=no
CORS_SAFE=no
CONFIG_RESULT=NO_GO
CORS_VALUE='https://www.absenteismocontroller.com.br'

restore_env() {
  if [ -n "${ENV_BACKUP:-}" ] && [ -f "$ENV_BACKUP" ]; then
    echo "RESTORE: restaurando .env a partir de $ENV_BACKUP"
    cp -a "$ENV_BACKUP" "$ENVF"
  else
    echo "RESTORE: backup .env indisponível — verificação manual necessária" >&2
  fi
}

fail() {
  echo "FAIL: $*" >&2
  CONFIG_RESULT=NO_GO
  restore_env
  echo "======== RESUMO ========"
  echo "CONFIG_BACKUP_DIR=${CONFIG_BACKUP_DIR:-}"
  echo "ENV_BACKUP=${ENV_BACKUP:-}"
  echo "GUNICORN_BACKUP=${GUNICORN_BACKUP:-}"
  echo "ENV_SHA_BEFORE=${ENV_SHA_BEFORE:-}"
  echo "ENV_SHA_AFTER=${ENV_SHA_AFTER:-}"
  echo "SECRET_KEY_PRESERVED=${SECRET_KEY_PRESERVED:-no}"
  echo "FLAGS_SAFE=${FLAGS_SAFE:-no}"
  echo "CORS_SAFE=${CORS_SAFE:-no}"
  echo "CONFIG_RESULT=NO_GO"
  exit 1
}

echo "=== FIT-08 BLOCO 2 — PREPARAR CONFIGURAÇÃO ==="

[ -d "$APP" ] || fail "APP ausente: $APP"
[ -f "$ENVF" ] || fail ".env ausente: $ENVF"
[ -f "$GUNI" ] || fail "gunicorn_config.py ausente: $GUNI"

# SECRET_KEY presente (valor nunca impresso)
if ! grep -Eq '^[[:space:]]*SECRET_KEY=.+' "$ENVF"; then
  fail "SECRET_KEY ausente ou vazia"
fi

secret_logical_sha() {
  # SHA do valor de SECRET_KEY apenas (não imprime o valor)
  local line val
  line=$(grep -E '^[[:space:]]*SECRET_KEY=' "$1" | tail -1) || return 1
  val=${line#*SECRET_KEY=}
  val=${val#[[:space:]]}
  [ -n "$val" ] || return 1
  printf '%s' "$val" | sha256sum | awk '{print $1}'
}

SK_SHA_BEFORE=$(secret_logical_sha "$ENVF") || fail "não foi possível hashear SECRET_KEY"
ENV_SHA_BEFORE=$(sha256sum "$ENVF" | awk '{print $1}')
GUNI_SHA_BEFORE=$(sha256sum "$GUNI" | awk '{print $1}')
echo "ENV_SHA_BEFORE=$ENV_SHA_BEFORE"
echo "GUNICORN_SHA_BEFORE=$GUNI_SHA_BEFORE"
echo "SECRET_KEY=PRESENT"

# Backup com preservação de permissões
mkdir -p "$CONFIG_BACKUP_DIR"
cp -a "$ENVF" "$CONFIG_BACKUP_DIR/.env"
cp -a "$GUNI" "$CONFIG_BACKUP_DIR/gunicorn_config.py"
ENV_BACKUP="$CONFIG_BACKUP_DIR/.env"
GUNICORN_BACKUP="$CONFIG_BACKUP_DIR/gunicorn_config.py"
echo "CONFIG_BACKUP_DIR=$CONFIG_BACKUP_DIR"
echo "ENV_BACKUP=$ENV_BACKUP"
echo "GUNICORN_BACKUP=$GUNICORN_BACKUP"

# Confirma SHA dos backups = originais
[ "$(sha256sum "$ENV_BACKUP" | awk '{print $1}')" = "$ENV_SHA_BEFORE" ] || fail "SHA backup .env diverge"
[ "$(sha256sum "$GUNICORN_BACKUP" | awk '{print $1}')" = "$GUNI_SHA_BEFORE" ] || fail "SHA backup gunicorn diverge"

# Owner/mode do .env vivo (para restaurar após mv atômico)
ENV_OWNER=$(stat -c '%u:%g' "$ENVF")
ENV_MODE=$(stat -c '%a' "$ENVF")

TMP=$(mktemp "$APP/.env.fit08.XXXXXX")
trap 'rm -f "$TMP"' EXIT

# Reescrita idempotente via Python (não imprime SECRET_KEY)
if ! python3 - "$ENVF" "$TMP" "$CORS_VALUE" <<'PY'
import re
import sys
from pathlib import Path

src, dst, cors = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
text = src.read_text(encoding="utf-8")
lines = text.splitlines()

wanted = {
    "ENVIRONMENT": "production",
    "ENABLE_INTELLIGENT_INGESTION": "false",
    "ENABLE_BIOMED_PERFORMANCE_ENGINE": "false",
    "ENABLE_API_DOCS": "false",
    "CORS_ALLOWED_ORIGINS": cors,
    "INGESTION_ALLOW_TEST_DEPENDENCIES": "false",
}
# Remove/empty: INGESTION_SQLITE_PATH must not point to live DB
clear_or_empty = {"INGESTION_SQLITE_PATH"}

seen = set()
out = []
for line in lines:
    m = re.match(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*)(.*)$", line)
    if not m:
        out.append(line)
        continue
    indent, key, eq, val = m.groups()
    seen.add(key)
    if key == "SECRET_KEY":
        if not str(val).strip():
            raise SystemExit("SECRET_KEY empty — abort")
        out.append(line)  # preserve exactly
    elif key in wanted:
        out.append(f"{indent}{key}{eq}{wanted[key]}")
    elif key in clear_or_empty:
        # leave key empty (idempotent; does not point to live DB)
        out.append(f"{indent}{key}{eq}")
    else:
        out.append(line)

for key, val in wanted.items():
    if key not in seen:
        out.append(f"{key}={val}")
if "INGESTION_SQLITE_PATH" not in seen:
    # optional: omit entirely if never present (safer than adding empty)
    pass
if "SECRET_KEY" not in seen:
    raise SystemExit("SECRET_KEY missing — abort")

dst.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
then
  fail "falha ao reescrever .env"
fi

# Substituição atômica + owner/mode
mv -f "$TMP" "$ENVF" || fail "falha na substituição atômica do .env"
trap - EXIT
chown "$ENV_OWNER" "$ENVF" || fail "falha ao restaurar owner do .env"
chmod "$ENV_MODE" "$ENVF" || fail "falha ao restaurar mode do .env"

ENV_SHA_AFTER=$(sha256sum "$ENVF" | awk '{print $1}')
SK_SHA_AFTER=$(secret_logical_sha "$ENVF") || fail "SECRET_KEY ausente após escrita"

get_env() {
  local line
  line=$(grep -E "^[[:space:]]*${1}=" "$ENVF" 2>/dev/null | tail -1 || true)
  if [ -z "$line" ]; then
    printf ''
    return 0
  fi
  printf '%s' "${line#*=}"
}

norm() { printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]'; }

ENV_VAL=$(get_env ENVIRONMENT)
ING_VAL=$(get_env ENABLE_INTELLIGENT_INGESTION)
PERF_VAL=$(get_env ENABLE_BIOMED_PERFORMANCE_ENGINE)
DOCS_VAL=$(get_env ENABLE_API_DOCS)
CORS_VAL=$(get_env CORS_ALLOWED_ORIGINS)
TESTDEP_VAL=$(get_env INGESTION_ALLOW_TEST_DEPENDENCIES)
INGPATH_VAL=$(get_env INGESTION_SQLITE_PATH)

echo "ENVIRONMENT=$ENV_VAL"
echo "ENABLE_INTELLIGENT_INGESTION=$ING_VAL"
echo "ENABLE_BIOMED_PERFORMANCE_ENGINE=$PERF_VAL"
echo "ENABLE_API_DOCS=$DOCS_VAL"
echo "CORS_ALLOWED_ORIGINS=$CORS_VAL"
echo "INGESTION_ALLOW_TEST_DEPENDENCIES=${TESTDEP_VAL:-}"
echo "INGESTION_SQLITE_PATH=${INGPATH_VAL:-EMPTY_OR_ABSENT}"
echo "SECRET_KEY=PRESENT"

[ "$(norm "$ENV_VAL")" = "production" ] || fail "ENVIRONMENT != production"

for pair in \
  "ENABLE_INTELLIGENT_INGESTION:$ING_VAL" \
  "ENABLE_BIOMED_PERFORMANCE_ENGINE:$PERF_VAL" \
  "ENABLE_API_DOCS:$DOCS_VAL" \
  "INGESTION_ALLOW_TEST_DEPENDENCIES:${TESTDEP_VAL:-false}"; do
  k=${pair%%:*}
  v=${pair#*:}
  nv=$(norm "$v")
  case "$nv" in false|0) ;; *) fail "flag insegura: $k=$v" ;; esac
done
FLAGS_SAFE=yes

[ "$CORS_VAL" = "$CORS_VALUE" ] || fail "CORS_ALLOWED_ORIGINS != oficial"
CORS_SAFE=yes

# INGESTION_SQLITE_PATH não pode apontar para banco vivo
if [ -n "${INGPATH_VAL:-}" ]; then
  case "$(norm "$INGPATH_VAL")" in
    */var/www/absenteismo/database/absenteismo.db*|*/database/absenteismo.db*)
      fail "INGESTION_SQLITE_PATH aponta para banco vivo"
      ;;
  esac
fi

if [ "$SK_SHA_BEFORE" = "$SK_SHA_AFTER" ]; then
  SECRET_KEY_PRESERVED=yes
else
  fail "SECRET_KEY alterada (SHA lógico diverge)"
fi

# gunicorn não deve ter sido tocado
[ "$(sha256sum "$GUNI" | awk '{print $1}')" = "$GUNI_SHA_BEFORE" ] || fail "gunicorn_config.py foi alterado indevidamente"

CONFIG_RESULT=GO

echo "======== RESUMO ========"
echo "CONFIG_BACKUP_DIR=$CONFIG_BACKUP_DIR"
echo "ENV_BACKUP=$ENV_BACKUP"
echo "GUNICORN_BACKUP=$GUNICORN_BACKUP"
echo "ENV_SHA_BEFORE=$ENV_SHA_BEFORE"
echo "ENV_SHA_AFTER=$ENV_SHA_AFTER"
echo "SECRET_KEY_PRESERVED=$SECRET_KEY_PRESERVED"
echo "FLAGS_SAFE=$FLAGS_SAFE"
echo "CORS_SAFE=$CORS_SAFE"
echo "CONFIG_RESULT=$CONFIG_RESULT"
