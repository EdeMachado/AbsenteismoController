#!/usr/bin/env bash
# RC-1.7 Block 5 — Restart absenteismocontroller.service only
#
# On failure: invoke code rollback via block7 (no automatic DB restore).
# USAGE:
#   sudo RC17_EXECUTE=1 bash scripts/rc17_block5_restart.sh
#
set -euo pipefail

if [[ "${RC17_EXECUTE:-}" != "1" ]]; then
  echo "REFUSING: set RC17_EXECUTE=1 to restart service." >&2
  exit 2
fi

APP_DIR="${APP_DIR:-/var/www/absenteismo}"
SERVICE="${SERVICE:-absenteismocontroller.service}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/api/health}"
STATE_DIR="${STATE_DIR:-/root/backups/absenteismo/rc17_state}"
ROLLBACK_SCRIPT="${ROLLBACK_SCRIPT:-$APP_DIR/scripts/rc17_block7_rollback.sh}"

echo "=== RC-1.7 BLOCK5 restart ==="
echo "SERVICE=$SERVICE"

systemctl restart "$SERVICE"
sleep 2

if ! systemctl is-active --quiet "$SERVICE"; then
  echo "FAIL: service not active after restart" >&2
  systemctl status "$SERVICE" --no-pager -l | head -n 60 || true
  journalctl -u "$SERVICE" -n 80 --no-pager || true
  echo "INITIATING CODE ROLLBACK"
  RC17_EXECUTE=1 bash "$ROLLBACK_SCRIPT"
  exit 1
fi

echo "ACTIVE=$(systemctl is-active "$SERVICE")"
journalctl -u "$SERVICE" -n 40 --no-pager || true

if command -v ss >/dev/null 2>&1; then
  ss -ltnp | grep -E ':8000\b' || {
    echo "FAIL: :8000 not listening" >&2
    RC17_EXECUTE=1 bash "$ROLLBACK_SCRIPT"
    exit 1
  }
fi

HEALTH_CODE="$(curl -s -o /tmp/rc17_health_post.json -w '%{http_code}' "$HEALTH_URL" || echo 000)"
echo "HEALTH_HTTP=$HEALTH_CODE"
if [[ "$HEALTH_CODE" != "200" ]]; then
  echo "FAIL: health not 200 after restart" >&2
  RC17_EXECUTE=1 bash "$ROLLBACK_SCRIPT"
  exit 1
fi

echo "BLOCK5_RESULT=GO"
