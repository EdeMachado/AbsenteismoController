#!/usr/bin/env bash
# RC-1.7 Block 3 — Update code (fast-forward only)
#
# Preserves: database/ .env gunicorn_config.py logs/ nohup.out
# FORBIDDEN: git reset --hard, git clean, migration, flag changes, .env edits
#
# USAGE (on VPS, AFTER Block2 GO + human authorization):
#   sudo RC17_EXECUTE=1 bash scripts/rc17_block3_update_code.sh
#
set -euo pipefail

if [[ "${RC17_EXECUTE:-}" != "1" ]]; then
  echo "REFUSING: set RC17_EXECUTE=1 to update code." >&2
  exit 2
fi

APP_DIR="${APP_DIR:-/var/www/absenteismo}"
TARGET_HEAD="${TARGET_HEAD:-fefa1996d37004c88dfb2087166544ea05be9e8f}"
STATE_DIR="${STATE_DIR:-/root/backups/absenteismo/rc17_state}"

cd "$APP_DIR"
mkdir -p "$STATE_DIR"

echo "=== RC-1.7 BLOCK3 update code ==="
git fetch origin main
ORIGIN_MAIN="$(git rev-parse origin/main)"
echo "ORIGIN_MAIN=$ORIGIN_MAIN"
if [[ "$ORIGIN_MAIN" != "$TARGET_HEAD" ]]; then
  echo "ABORT: origin/main != TARGET_HEAD ($ORIGIN_MAIN != $TARGET_HEAD)" >&2
  exit 3
fi

OLD_HEAD="$(git rev-parse HEAD)"
echo "OLD_HEAD=$OLD_HEAD"
echo "$OLD_HEAD" > "$STATE_DIR/OLD_HEAD.txt"
echo "$TARGET_HEAD" > "$STATE_DIR/TARGET_HEAD.txt"

# Ensure preserve targets exist / are not deleted by us
for p in database .env gunicorn_config.py logs nohup.out; do
  if [[ -e "$p" ]]; then
    echo "PRESERVE=$p"
  else
    echo "ABSENT_OK=$p"
  fi
done

# Tracked tree must be clean before FF
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "ABORT: tracked working tree dirty" >&2
  git status --porcelain --untracked-files=no >&2
  exit 4
fi

# Fast-forward only to origin/main (exact TARGET_HEAD)
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "BRANCH=$CURRENT_BRANCH"

if git merge-base --is-ancestor HEAD origin/main; then
  :
else
  echo "ABORT: HEAD is not ancestor of origin/main — refuse non-FF" >&2
  exit 5
fi

# Prefer merge --ff-only from origin/main (no reset --hard, no clean)
git merge --ff-only origin/main

NEW_HEAD="$(git rev-parse HEAD)"
echo "NEW_HEAD=$NEW_HEAD"
if [[ "$NEW_HEAD" != "$TARGET_HEAD" ]]; then
  echo "ABORT: HEAD after update != TARGET_HEAD ($NEW_HEAD != $TARGET_HEAD)" >&2
  exit 6
fi

# Reconfirm preserves still present
for p in database .env; do
  if [[ ! -e "$p" ]]; then
    echo "ABORT: preserved path missing after update: $p" >&2
    exit 7
  fi
done

echo "BLOCK3_RESULT=GO"
echo "OLD_HEAD=$OLD_HEAD"
echo "NEW_HEAD=$NEW_HEAD"
