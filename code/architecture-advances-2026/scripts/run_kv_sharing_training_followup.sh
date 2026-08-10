#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.training_matrix \
  --root-dir "$ROOT_DIR" \
  --artifact-out "$ROOT_DIR/artifacts/reports/kv-sharing-training-followup.json" \
  --variant kv_sharing \
  --batch-size 4 \
  --seq-len 8 \
  --seq-len 16 \
  --steps 4 \
  --seed 17 \
  --seed 23 \
  --lr 0.01 \
  --clip-grad-norm 1.0 \
  --report-runs 1
