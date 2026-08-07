#!/usr/bin/env bash
# EXEC-02 isolated staging — synthetic DB only. Never production.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export ABSENTEISMO_SQLITE_PATH="${ABSENTEISMO_SQLITE_PATH:-$ROOT/database/exec02_synth.sqlite}"
export SECRET_KEY="${SECRET_KEY:-exec02-staging-secret-not-for-production}"
export ENVIRONMENT=staging
export ENABLE_EXECUTIVE_UI=true
export ENABLE_INTELLIGENT_INGESTION=false
export ENABLE_BIOMED_PERFORMANCE_ENGINE=false
export EXECUTIVE_STAGING_DEMO=true
export PORT="${PORT:-18082}"
cd "$ROOT"
echo "EXEC-02 staging on :$PORT  db=$ABSENTEISMO_SQLITE_PATH  flag=ON"
exec python3 -m uvicorn backend.main:app --host 127.0.0.1 --port "$PORT"
