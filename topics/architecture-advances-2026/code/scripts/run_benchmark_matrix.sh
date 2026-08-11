#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.benchmark_matrix \
  --root-dir "$ROOT_DIR" \
  --batch-size 1 \
  --batch-size 2 \
  --seq-len 4 \
  --seq-len 8 \
  --seq-len 16 \
  --warmup-runs 1 \
  --measured-runs 3 \
  --report-runs 3 \
  --artifact-json "$ROOT_DIR/artifacts/reports/micro-benchmark-matrix.json" \
  --artifact-md "$ROOT_DIR/artifacts/reports/micro-benchmark-matrix.md" \
  --stdout
