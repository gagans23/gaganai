#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$HOME/.openclaw/service-env/ai.openclaw.gateway.env"
PYTHON_BIN="${PYTHON_BIN:-$ROOT/../mirage-py-lab/.venv/bin/python}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

cd "$ROOT"
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python runtime not found at $PYTHON_BIN"
  echo "Set PYTHON_BIN or install the Mirage virtualenv alongside the repo."
  exit 1
fi
"$PYTHON_BIN" automation/gcc-ai-newsletter/run_daily.py --window-hours 24 "$@"
