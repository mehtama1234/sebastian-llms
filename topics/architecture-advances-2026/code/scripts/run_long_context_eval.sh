#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

if [ ! -f "$ROOT_DIR/artifacts/long_context/synthetic_cases.jsonl" ]; then
  "$ROOT_DIR/scripts/generate_long_context_cases.sh" >/dev/null
fi

"$VENV_PYTHON" -m arch_adv_2026.long_context_eval_cli \
  --model-id "Qwen/Qwen3-0.6B" \
  --cases "$ROOT_DIR/artifacts/long_context/synthetic_cases.jsonl" \
  --artifact "$ROOT_DIR/artifacts/long_context/qwen3_long_context_eval.json" \
  --stdout
