#!/usr/bin/env bash
# RC-1.7 Block 2 — Mandatory pre-change backup
#
# Backs up: database/absenteismo.db, .env, gunicorn_config.py
# DOES NOT: restart, pull, migrate, alter live DB, print secrets.
# DOES NOT: delete/overwrite previous backups.
#
# USAGE (on VPS, AFTER Block1 GO and human authorization):
#   sudo RC17_EXECUTE=1 bash scripts/rc17_block2_backup.sh
#
set -euo pipefail

if [[ "${RC17_EXECUTE:-}" != "1" ]]; then
  echo "REFUSING: set RC17_EXECUTE=1 to run backup (preparation-only otherwise)." >&2
  exit 2
fi

APP_DIR="${APP_DIR:-/var/www/absenteismo}"
LIVE_DB="${LIVE_DB:-/var/www/absenteismo/database/absenteismo.db}"
BACKUP_ROOT="${BACKUP_ROOT:-/root/backups/absenteismo}"
VENV_PY="${VENV_PY:-$APP_DIR/venv/bin/python}"
TS="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$BACKUP_ROOT/rc17_predeploy_$TS"
BACKUP_DB="$OUT_DIR/absenteismo_pre_rc17_${TS}.db"
ENV_BAK="$OUT_DIR/dotenv.env"
GUNI_BAK="$OUT_DIR/gunicorn_config.py"
MANIFEST="$OUT_DIR/MANIFEST.txt"

if [[ "${FORCE_NONPROD:-}" != "1" ]]; then
  if [[ "$LIVE_DB" != "/var/www/absenteismo/database/absenteismo.db" ]]; then
    echo "REFUSING: LIVE_DB is not known production path." >&2
    exit 2
  fi
fi

echo "=== RC-1.7 BLOCK2 backup ==="
echo "TS=$TS"
echo "OUT_DIR=$OUT_DIR"
mkdir -p "$OUT_DIR"

test -f "$LIVE_DB"
test -x "$VENV_PY"

echo "--- live integrity (read-only) ---"
"$VENV_PY" - <<PY
import json, sqlite3, sys
live = ${LIVE_DB@Q}
conn = sqlite3.connect(f"file:{live}?mode=ro", uri=True)
cur = conn.cursor()
quick = cur.execute("PRAGMA quick_check;").fetchone()[0]
integrity = cur.execute("PRAGMA integrity_check;").fetchone()[0]
print(json.dumps({"quick_check": quick, "integrity_check": integrity}, ensure_ascii=False))
if str(quick).lower() != "ok" or str(integrity).lower() != "ok":
    sys.exit(4)
conn.close()
PY

echo "--- sqlite3.Connection.backup ---"
if [[ -e "$BACKUP_DB" ]]; then
  echo "REFUSING: backup already exists $BACKUP_DB" >&2
  exit 5
fi
"$VENV_PY" - <<PY
import os, sqlite3
src = ${LIVE_DB@Q}
dst = ${BACKUP_DB@Q}
src_conn = sqlite3.connect(src)
dst_conn = sqlite3.connect(dst)
try:
    src_conn.backup(dst_conn)
finally:
    dst_conn.close()
    src_conn.close()
print("BACKUP_OK", dst)
PY

echo "--- validate backup ---"
"$VENV_PY" - <<PY
import json, os, sqlite3, sys
bak = ${BACKUP_DB@Q}
conn = sqlite3.connect(f"file:{bak}?mode=ro", uri=True)
cur = conn.cursor()
quick = cur.execute("PRAGMA quick_check;").fetchone()[0]
integrity = cur.execute("PRAGMA integrity_check;").fetchone()[0]
print(json.dumps({"backup_quick_check": quick, "backup_integrity_check": integrity}, ensure_ascii=False))
if str(quick).lower() != "ok" or str(integrity).lower() != "ok":
    sys.exit(6)
print("size_bytes", os.path.getsize(bak))
conn.close()
PY

DB_SHA="$(sha256sum "$BACKUP_DB" | awk '{print $1}')"
DB_SIZE="$(stat -c%s "$BACKUP_DB")"
DB_PERM="$(stat -c%a "$BACKUP_DB")"
echo "$DB_SHA  $(basename "$BACKUP_DB")" > "${BACKUP_DB}.sha256"

# .env and gunicorn_config — copy without echoing contents
if [[ -f "$APP_DIR/.env" ]]; then
  cp -a "$APP_DIR/.env" "$ENV_BAK"
  ENV_SHA="$(sha256sum "$ENV_BAK" | awk '{print $1}')"
  ENV_SIZE="$(stat -c%s "$ENV_BAK")"
  ENV_PERM="$(stat -c%a "$ENV_BAK")"
  echo "$ENV_SHA  dotenv.env" > "${ENV_BAK}.sha256"
else
  ENV_SHA="MISSING"
  ENV_SIZE=0
  ENV_PERM="-"
  echo "WARN: .env missing at backup time" >&2
fi

if [[ -f "$APP_DIR/gunicorn_config.py" ]]; then
  cp -a "$APP_DIR/gunicorn_config.py" "$GUNI_BAK"
  GUNI_SHA="$(sha256sum "$GUNI_BAK" | awk '{print $1}')"
  GUNI_SIZE="$(stat -c%s "$GUNI_BAK")"
  GUNI_PERM="$(stat -c%a "$GUNI_BAK")"
  echo "$GUNI_SHA  gunicorn_config.py" > "${GUNI_BAK}.sha256"
else
  GUNI_SHA="MISSING"
  GUNI_SIZE=0
  GUNI_PERM="-"
  echo "WARN: gunicorn_config.py missing at backup time" >&2
fi

{
  echo "RC17_BACKUP_MANIFEST"
  echo "timestamp=$TS"
  echo "out_dir=$OUT_DIR"
  echo "db_path=$BACKUP_DB"
  echo "db_sha256=$DB_SHA"
  echo "db_size_bytes=$DB_SIZE"
  echo "db_perm=$DB_PERM"
  echo "env_path=$ENV_BAK"
  echo "env_sha256=$ENV_SHA"
  echo "env_size_bytes=$ENV_SIZE"
  echo "env_perm=$ENV_PERM"
  echo "gunicorn_path=$GUNI_BAK"
  echo "gunicorn_sha256=$GUNI_SHA"
  echo "gunicorn_size_bytes=$GUNI_SIZE"
  echo "gunicorn_perm=$GUNI_PERM"
  echo "note=SECRET_KEY_and_file_contents_not_printed"
} | tee "$MANIFEST"

ls -la "$OUT_DIR"
echo "BLOCK2_RESULT=GO"
echo "BACKUP_DIR=$OUT_DIR"
