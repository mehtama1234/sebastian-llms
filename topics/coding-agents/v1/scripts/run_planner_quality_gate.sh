#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_DIR}"

if [[ -z "${CODING_AGENT_V1_MODEL_PLANNER_COMMAND:-}" ]]; then
  echo "CODING_AGENT_V1_MODEL_PLANNER_COMMAND is required for the model-guided candidate run" >&2
  echo "Example: export CODING_AGENT_V1_MODEL_PLANNER_COMMAND=\"python3 -m coding_agent_v1.model_planner_adapter\"" >&2
  exit 2
fi

PACK_PATH="../../evals/coding-agent-v1/scenarios/planner-quality-v1.json"
RUN_ID="$(date +%Y%m%d-%H%M%S)"
SESSION_DIR="${1:-.coding-agent-v1/planner-quality-gate-${RUN_ID}}"
ARTIFACT_DIR="${SESSION_DIR}/eval-artifacts"

echo "==> Planner-quality gate session dir: ${SESSION_DIR}"

echo "==> Running deterministic planner-quality baseline"
PYTHONPATH=src python3 -m coding_agent_v1.cli \
  --session-dir "${SESSION_DIR}" \
  --run-eval-pack "${PACK_PATH}" \
  --eval-label planner-quality-baseline

echo "==> Running model-guided planner-quality candidate"
PYTHONPATH=src python3 -m coding_agent_v1.cli \
  --session-dir "${SESSION_DIR}" \
  --run-eval-pack "${PACK_PATH}" \
  --eval-planner-strategy model_guided \
  --eval-label planner-quality-model-guided-candidate

echo "==> Comparing model-guided candidate against deterministic baseline"
comparison_output="$(
  PYTHONPATH=src python3 -m coding_agent_v1.cli \
    --session-dir "${SESSION_DIR}" \
    --compare-evals planner-quality-baseline planner-quality-model-guided-candidate
)"
printf '%s\n' "${comparison_output}"

regressions="$(printf '%s\n' "${comparison_output}" | awk -F': ' '/^regressions:/ {print $2; exit}')"
expectation_regressions="$(printf '%s\n' "${comparison_output}" | awk -F': ' '/^expectation_regressions:/ {print $2; exit}')"

if [[ "${regressions}" != "0" ]]; then
  echo "planner-quality gate failed: regressions=${regressions}" >&2
  exit 1
fi

if [[ "${expectation_regressions}" != "0" ]]; then
  echo "planner-quality gate failed: expectation_regressions=${expectation_regressions}" >&2
  exit 1
fi

echo "==> Planner-quality gate passed"
echo "artifact_dir: ${ARTIFACT_DIR}"
