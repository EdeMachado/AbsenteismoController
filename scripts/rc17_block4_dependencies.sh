#!/usr/bin/env bash
# RC-1.7 Block 4 — Dependencies + compile + import + route inventory
#
# Uses production venv only. Does not restart service.
# USAGE:
#   sudo RC17_EXECUTE=1 bash scripts/rc17_block4_dependencies.sh
#
set -euo pipefail

if [[ "${RC17_EXECUTE:-}" != "1" ]]; then
  echo "REFUSING: set RC17_EXECUTE=1 to install/validate deps." >&2
  exit 2
fi

APP_DIR="${APP_DIR:-/var/www/absenteismo}"
VENV_PY="${VENV_PY:-$APP_DIR/venv/bin/python}"
VENV_PIP="${VENV_PIP:-$APP_DIR/venv/bin/pip}"

cd "$APP_DIR"
test -x "$VENV_PY"
test -x "$VENV_PIP"

echo "=== RC-1.7 BLOCK4 dependencies ==="
echo "VENV_PY=$VENV_PY"

"$VENV_PIP" install -r requirements.txt

echo "--- compileall ---"
"$VENV_PY" -m compileall -q backend
echo "COMPILE=PASS"

echo "--- import backend.main ---"
# Load .env into process without printing values
set -a
# shellcheck disable=SC1091
[[ -f "$APP_DIR/.env" ]] && . "$APP_DIR/.env"
set +a
# Ensure production-like flags for import-time registration
export ENVIRONMENT="${ENVIRONMENT:-production}"
export ENABLE_EXECUTIVE_UI="${ENABLE_EXECUTIVE_UI:-false}"
export ENABLE_EXECUTIVE_PRESENTATION="${ENABLE_EXECUTIVE_PRESENTATION:-false}"
export ENABLE_INTELLIGENT_INGESTION="${ENABLE_INTELLIGENT_INGESTION:-false}"
export ENABLE_BIOMED_PERFORMANCE_ENGINE="${ENABLE_BIOMED_PERFORMANCE_ENGINE:-false}"
export ENABLE_API_DOCS="${ENABLE_API_DOCS:-false}"
export ENABLE_PREVIEW_SURFACES="${ENABLE_PREVIEW_SURFACES:-false}"

"$VENV_PY" - <<'PY'
import backend.main
print("IMPORT=PASS", backend.main.app.title)
print("ROUTES", len(backend.main.app.routes))
PY

echo "--- route inventory (known registry) ---"
"$VENV_PY" - <<'PY'
from backend.main import app
from backend.route_security_registry import inventory_unclassified

bad = inventory_unclassified(app)
if bad:
    raise SystemExit(f"ROUTE_INVENTORY_FAIL: {bad}")
print("ROUTE_INVENTORY=PASS")
PY

echo "BLOCK4_RESULT=GO"
