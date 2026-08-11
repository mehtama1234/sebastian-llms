#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.long_context_projection \
  --sweep-artifact "$ROOT_DIR/artifacts/long_context/qwen3_long_context_medium.json" \
  --baseline-config "$ROOT_DIR/configs/qwen3-baseline.json" \
  --variant-configs \
    "$ROOT_DIR/configs/qwen3-kv-sharing.json" \
    "$ROOT_DIR/configs/qwen3-attention-budgeting.json" \
    "$ROOT_DIR/configs/qwen3-compressed-attention.json" \
    "$ROOT_DIR/configs/qwen3-history-compression.json" \
    "$ROOT_DIR/configs/qwen3-mhc.json" \
    "$ROOT_DIR/configs/qwen3-ple.json" \
  --artifact "$ROOT_DIR/artifacts/long_context/qwen3_long_context_medium_qwen_projection.json" \
  --stdout
