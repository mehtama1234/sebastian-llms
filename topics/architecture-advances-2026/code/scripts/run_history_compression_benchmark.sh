#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.benchmark_cli \
  --baseline-config "$ROOT_DIR/configs/micro-baseline.json" \
  --variant-config "$ROOT_DIR/configs/micro-history-compression.json" \
  --artifact "$ROOT_DIR/artifacts/benchmarks/micro-baseline-vs-history-compression.json" \
  --stdout
