#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.compressed_attention_training_diagnosis \
  --matrix "$ROOT_DIR/artifacts/reports/compressed-attention-training-followup.json" \
  --artifact-json "$ROOT_DIR/artifacts/reports/compressed-attention-training-diagnosis.json" \
  --artifact-md "$ROOT_DIR/artifacts/reports/compressed-attention-training-diagnosis.md" \
  --stdout
