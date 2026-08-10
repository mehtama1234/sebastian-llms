#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

# Refresh the systems-side upstream artifacts first so the decision layer
# does not consume a stale micro report or benchmark matrix.
"$ROOT_DIR/scripts/run_variant_report.sh" >/dev/null
"$ROOT_DIR/scripts/run_benchmark_matrix.sh" >/dev/null

"$VENV_PYTHON" -m arch_adv_2026.decision_stack \
  --micro-report "$ROOT_DIR/artifacts/reports/micro-variant-report.json" \
  --benchmark-matrix "$ROOT_DIR/artifacts/reports/micro-benchmark-matrix.json" \
  --long-context-compare "$ROOT_DIR/artifacts/long_context/qwen3_variant_proxy_compare.json" \
  --training-matrix "$ROOT_DIR/artifacts/reports/micro-training-matrix.json" \
  --seed-final-memo "$ROOT_DIR/artifacts/reports/final-architecture-memo.json" \
  --long-context-selector "$ROOT_DIR/artifacts/long_context/qwen3_variant_proxy_selector.json" \
  --long-context-execution "$ROOT_DIR/artifacts/plans/qwen3-quality_preserving_memory-variant-proxy-execution.json" \
  --followup-assessment "$ROOT_DIR/artifacts/reports/attention-budgeting-training-assessment.json" \
  --followup-assessment "$ROOT_DIR/artifacts/reports/kv-sharing-training-assessment.json" \
  --followup-assessment "$ROOT_DIR/artifacts/reports/kv-sharing-long-context-assessment.json" \
  --scorecard-json "$ROOT_DIR/artifacts/reports/architecture-concept-scorecard.json" \
  --scorecard-md "$ROOT_DIR/artifacts/reports/architecture-concept-scorecard.md" \
  --audit-json "$ROOT_DIR/artifacts/reports/architecture-concept-decision-audit.json" \
  --audit-md "$ROOT_DIR/artifacts/reports/architecture-concept-decision-audit.md" \
  --review-plan-json "$ROOT_DIR/artifacts/reports/architecture-concept-review-plan.json" \
  --review-plan-md "$ROOT_DIR/artifacts/reports/architecture-concept-review-plan.md" \
  --final-memo-json "$ROOT_DIR/artifacts/reports/final-architecture-memo.json" \
  --final-memo-md "$ROOT_DIR/artifacts/reports/final-architecture-memo.md" \
  --stdout

bash "$ROOT_DIR/scripts/run_decision_stack_validate.sh" >/dev/null
