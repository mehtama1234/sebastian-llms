#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.training_report_cli \
  --root-dir "$ROOT_DIR" \
  --artifact "$ROOT_DIR/artifacts/reports/micro-training-report.json" \
  --batch-size 4 \
  --seq-len 8 \
  --steps 4 \
  --lr 0.01 \
  --seed 17 \
  --clip-grad-norm 1.0 \
  --report-runs 1 \
  --stdout
