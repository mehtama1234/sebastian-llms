#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.concept_scorecard \
  --micro-report "$ROOT_DIR/artifacts/reports/micro-variant-report.json" \
  --benchmark-matrix "$ROOT_DIR/artifacts/reports/micro-benchmark-matrix.json" \
  --long-context-compare "$ROOT_DIR/artifacts/long_context/qwen3_variant_proxy_compare.json" \
  --training-matrix "$ROOT_DIR/artifacts/reports/micro-training-matrix.json" \
  --final-memo "$ROOT_DIR/artifacts/reports/final-architecture-memo.json" \
  --artifact-json "$ROOT_DIR/artifacts/reports/architecture-concept-scorecard.json" \
  --artifact-md "$ROOT_DIR/artifacts/reports/architecture-concept-scorecard.md" \
  --stdout
