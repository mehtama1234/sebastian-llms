#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.training_benchmark_cli \
  --baseline-config "$ROOT_DIR/configs/micro-baseline.json" \
  --variant-config "$ROOT_DIR/configs/micro-compressed-attention.json" \
  --batch-size 8 \
  --seq-len 16 \
  --steps 8 \
  --lr 0.01 \
  --seed 17 \
  --clip-grad-norm 1.0 \
  --artifact "$ROOT_DIR/artifacts/benchmarks/micro-baseline-vs-compressed_attention-training.json" \
  --stdout
