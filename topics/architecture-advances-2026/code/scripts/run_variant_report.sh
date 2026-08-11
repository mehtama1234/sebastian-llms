#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.report_cli \
  --root-dir "$ROOT_DIR" \
  --artifact "$ROOT_DIR/artifacts/reports/micro-variant-report.json" \
  --seq-len 8 \
  --warmup-runs 1 \
  --measured-runs 5 \
  --stdout
