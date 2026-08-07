#!/usr/bin/env bash
# RC-1.7 Block 7 — Code rollback (NO automatic DB restore)
#
# Restores git HEAD to OLD_HEAD recorded by Block3 (or RC17_OLD_HEAD env).
# Restores .env / gunicorn_config.py from backup ONLY if RC17_RESTORE_CONFIG=1
# and RC17_BACKUP_DIR points to Block2 output.
#
# USAGE:
#   sudo RC17_EXECUTE=1 bash scripts/rc17_block7_rollback.sh
#
set -euo pipefail

if [[ "${RC17_EXECUTE:-}" != "1" ]]; then
  echo "REFUSING: set RC17_EXECUTE=1 to rollback code." >&2
  exit 2
fi

APP_DIR="${APP_DIR:-/var/www/absenteismo}"
SERVICE="${SERVICE:-absenteismocontroller.service}"
STATE_DIR="${STATE_DIR:-/root/backups/absenteismo/rc17_state}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/api/health}"
OLD_HEAD="${RC17_OLD_HEAD:-}"

if [[ -z "$OLD_HEAD" && -f "$STATE_DIR/OLD_HEAD.txt" ]]; then
  OLD_HEAD="$(tr -d '[:space:]' < "$STATE_DIR/OLD_HEAD.txt")"
fi
if [[ -z "$OLD_HEAD" ]]; then
  echo "ABORT: OLD_HEAD unknown (set RC17_OLD_HEAD or run Block3 first)" >&2
  exit 3
fi

cd "$APP_DIR"
echo "=== RC-1.7 BLOCK7 code rollback ==="
echo "OLD_HEAD=$OLD_HEAD"
echo "CURRENT_HEAD=$(git rev-parse HEAD)"

git fetch origin --quiet || true

# Checkout previous SHA without clean / without hard reset of untracked
git checkout "$OLD_HEAD"

# Optional config restore (explicit)
if [[ "${RC17_RESTORE_CONFIG:-}" == "1" ]]; then
  BAK="${RC17_BACKUP_DIR:-}"
  if [[ -z "$BAK" || ! -d "$BAK" ]]; then
    echo "ABORT: RC17_RESTORE_CONFIG=1 but RC17_BACKUP_DIR missing" >&2
    exit 4
  fi
  if [[ -f "$BAK/dotenv.env" ]]; then
    cp -a "$BAK/dotenv.env" "$APP_DIR/.env"
    echo "RESTORED=.env (contents not printed)"
  fi
  if [[ -f "$BAK/gunicorn_config.py" ]]; then
    cp -a "$BAK/gunicorn_config.py" "$APP_DIR/gunicorn_config.py"
    echo "RESTORED=gunicorn_config.py"
  fi
else
  echo "CONFIG_RESTORE=skipped (set RC17_RESTORE_CONFIG=1 to enable)"
fi

echo "DB_RESTORE=skipped (human decision required; never automatic)"

systemctl restart "$SERVICE"
sleep 2
systemctl is-active --quiet "$SERVICE"
HEALTH_CODE="$(curl -s -o /dev/null -w '%{http_code}' "$HEALTH_URL" || echo 000)"
echo "HEALTH_HTTP=$HEALTH_CODE"
if [[ "$HEALTH_CODE" != "200" ]]; then
  echo "BLOCK7_RESULT=NO_GO health=$HEALTH_CODE" >&2
  journalctl -u "$SERVICE" -n 80 --no-pager || true
  exit 1
fi

echo "ROLLED_BACK_HEAD=$(git rev-parse HEAD)"
echo "BLOCK7_RESULT=GO"
