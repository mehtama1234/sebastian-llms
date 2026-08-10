#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.long_context_report \
  --artifact "$ROOT_DIR/artifacts/long_context/qwen3_long_context_sweep_agg_smoke.json" \
  --markdown-out "$ROOT_DIR/artifacts/long_context/qwen3_long_context_sweep_agg_smoke.md" \
  --stdout
