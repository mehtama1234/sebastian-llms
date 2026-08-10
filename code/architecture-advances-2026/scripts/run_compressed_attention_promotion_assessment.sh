#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.compressed_attention_promotion_assessment \
  --training-matrix "$ROOT_DIR/artifacts/reports/compressed-attention-training-followup.json" \
  --benchmark-matrix "$ROOT_DIR/artifacts/reports/compressed-attention-promotion-benchmark-matrix.json" \
  --long-context-execution "$ROOT_DIR/artifacts/plans/qwen3-quality_preserving_memory-variant-proxy-execution.json" \
  --artifact-json "$ROOT_DIR/artifacts/reports/compressed-attention-promotion-assessment.json" \
  --artifact-md "$ROOT_DIR/artifacts/reports/compressed-attention-promotion-assessment.md" \
  --stdout
