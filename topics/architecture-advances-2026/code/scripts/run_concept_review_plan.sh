#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.concept_review_plan \
  --scorecard "$ROOT_DIR/artifacts/reports/architecture-concept-scorecard.json" \
  --audit "$ROOT_DIR/artifacts/reports/architecture-concept-decision-audit.json" \
  --followup-assessment "$ROOT_DIR/artifacts/reports/attention-budgeting-training-assessment.json" \
  --followup-assessment "$ROOT_DIR/artifacts/reports/kv-sharing-training-assessment.json" \
  --followup-assessment "$ROOT_DIR/artifacts/reports/kv-sharing-long-context-assessment.json" \
  --artifact-json "$ROOT_DIR/artifacts/reports/architecture-concept-review-plan.json" \
  --artifact-md "$ROOT_DIR/artifacts/reports/architecture-concept-review-plan.md" \
  --stdout
