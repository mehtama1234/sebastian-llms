#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.decision_stack_validate \
  --audit "$ROOT_DIR/artifacts/reports/architecture-concept-decision-audit.json" \
  --review-plan "$ROOT_DIR/artifacts/reports/architecture-concept-review-plan.json" \
  --final-memo "$ROOT_DIR/artifacts/reports/final-architecture-memo.json" \
  --stdout
