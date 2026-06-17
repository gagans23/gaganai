#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"
ENV_FILE="$HOME/.openclaw/service-env/ai.openclaw.gateway.env"
LOCAL_ENV_FILE="$REPO_ROOT/.env"
WINDOW_HOURS="${WINDOW_HOURS:-24}"
DRY_RUN="${DRY_RUN:-0}"
ISSUE_DATE="${ISSUE_DATE:-}"
SITE_REPO="$REPO_ROOT"
# Publish ONLY raw data. Never baked pages or design assets.
# The GitHub Actions "Bake radar edition" workflow rebuilds radar.html, feed.xml
# and the radar/ archive FRESH from origin on every data push — so no local clone
# (stale or not) can ever publish stale HTML or revert the site's design.
PUBLISH_FILES=(
  data/radar-signals.js
  data/podcast-intelligence.js
  data/signal-archive.json
)

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi
if [[ -f "$LOCAL_ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$LOCAL_ENV_FILE"
  set +a
fi
if [[ -z "${PYTHON_BIN:-}" ]]; then
  if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
    PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi

cd "$REPO_ROOT"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 && [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python runtime not found at $PYTHON_BIN"
  echo "Run 'make setup' or set PYTHON_BIN."
  exit 1
fi
ARGS=(--window-hours "$WINDOW_HOURS")
if [[ "$DRY_RUN" == "1" ]]; then
  ARGS+=(--dry-run)
fi
if [[ -n "$ISSUE_DATE" ]]; then
  ARGS+=(--issue-date "$ISSUE_DATE")
fi

"$PYTHON_BIN" automation/gcc-ai-newsletter/run_daily.py "${ARGS[@]}"

# NOTE: no local bake. CI ("Bake radar edition") rebuilds radar.html/feed/archive
# from origin after this pushes the data. This is deliberate — see PUBLISH_FILES.

cd "$SITE_REPO"
if git diff --quiet -- "${PUBLISH_FILES[@]}"; then
  echo "No intelligence changes to publish."
  exit 0
fi

if [[ "$DRY_RUN" == "1" ]]; then
  git status --short -- "${PUBLISH_FILES[@]}"
  exit 0
fi

git fetch origin main
TMP_WORKTREE="$(mktemp -d "${TMPDIR:-/tmp}/gaganai-publish.XXXXXX")"
cleanup() {
  git -C "$SITE_REPO" worktree remove --force "$TMP_WORKTREE" >/dev/null 2>&1 || true
}
trap cleanup EXIT

git worktree add --detach "$TMP_WORKTREE" origin/main >/dev/null

for relpath in "${PUBLISH_FILES[@]}"; do
  if [[ -f "$SITE_REPO/$relpath" ]]; then
    mkdir -p "$TMP_WORKTREE/$(dirname "$relpath")"
    cp "$SITE_REPO/$relpath" "$TMP_WORKTREE/$relpath"
  fi
done

cd "$TMP_WORKTREE"
ADD_PATHS=()
for relpath in "${PUBLISH_FILES[@]}"; do
  [[ -f "$relpath" ]] && ADD_PATHS+=("$relpath")
done
git add -- "${ADD_PATHS[@]}"
if git diff --cached --quiet; then
  echo "No website data changes to publish after syncing with origin/main."
  exit 0
fi
git commit -m "Daily intelligence refresh $(date +%Y-%m-%d)"
git push origin HEAD:main
