#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.torch_demo \
  --config "$ROOT_DIR/configs/micro-baseline.json" \
  --artifact "$ROOT_DIR/artifacts/torch/micro-baseline.json" \
  --stdout

"$VENV_PYTHON" -m arch_adv_2026.torch_demo \
  --config "$ROOT_DIR/configs/micro-kv-sharing.json" \
  --artifact "$ROOT_DIR/artifacts/torch/micro-kv-sharing.json" \
  --stdout
