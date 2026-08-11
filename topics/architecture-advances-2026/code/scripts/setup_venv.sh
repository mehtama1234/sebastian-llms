#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV_DIR/bin/pip" install -e "$ROOT_DIR"
"$VENV_DIR/bin/pip" install -e "$ROOT_DIR[hf]"

cat <<EOF
Created venv at:
  $VENV_DIR

Example commands:
  $VENV_DIR/bin/python -m pytest $ROOT_DIR/tests
  $ROOT_DIR/scripts/run_model_summary.sh
  $ROOT_DIR/scripts/run_numeric_demo.sh
  $ROOT_DIR/scripts/run_numeric_benchmark.sh
  $ROOT_DIR/scripts/run_qwen_reference_inspect.sh
  $ROOT_DIR/scripts/run_qwen_reference_eval.sh
  $ROOT_DIR/scripts/generate_long_context_cases.sh
  $ROOT_DIR/scripts/run_long_context_eval.sh
  $ROOT_DIR/scripts/run_long_context_sweep.sh
  $ROOT_DIR/scripts/run_long_context_report.sh
  $ROOT_DIR/scripts/run_long_context_projection.sh
  $ROOT_DIR/scripts/run_long_context_projection_report.sh
  $ROOT_DIR/scripts/run_long_context_compare.sh
EOF
