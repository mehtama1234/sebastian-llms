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

PACK_PATH="../../evals/coding-agent-v1/scenarios/planner-quality-v2.json"
RUN_ID="$(date +%Y%m%d-%H%M%S)"
SESSION_DIR="${1:-.coding-agent-v1/planner-superiority-gate-${RUN_ID}}"
ARTIFACT_DIR="${SESSION_DIR}/eval-artifacts"
MIN_IMPROVEMENTS="${PLANNER_SUPERIORITY_MIN_IMPROVEMENTS:-1}"

echo "==> Planner-superiority gate session dir: ${SESSION_DIR}"

echo "==> Running deterministic planner-superiority baseline"
PYTHONPATH=src python3 -m coding_agent_v1.cli \
  --session-dir "${SESSION_DIR}" \
  --run-eval-pack "${PACK_PATH}" \
  --eval-label planner-superiority-baseline

echo "==> Running model-guided planner-superiority candidate"
PYTHONPATH=src python3 -m coding_agent_v1.cli \
  --session-dir "${SESSION_DIR}" \
  --run-eval-pack "${PACK_PATH}" \
  --eval-planner-strategy model_guided \
  --eval-label planner-superiority-model-guided-candidate

echo "==> Comparing model-guided candidate against deterministic baseline"
comparison_output="$(
  PYTHONPATH=src python3 -m coding_agent_v1.cli \
    --session-dir "${SESSION_DIR}" \
    --compare-evals planner-superiority-baseline planner-superiority-model-guided-candidate
)"
printf '%s\n' "${comparison_output}"

regressions="$(printf '%s\n' "${comparison_output}" | awk -F': ' '/^regressions:/ {print $2; exit}')"
expectation_regressions="$(printf '%s\n' "${comparison_output}" | awk -F': ' '/^expectation_regressions:/ {print $2; exit}')"
improvements="$(printf '%s\n' "${comparison_output}" | awk -F': ' '/^improvements:/ {print $2; exit}')"

if [[ "${regressions}" != "0" ]]; then
  echo "planner-superiority gate failed: regressions=${regressions}" >&2
  exit 1
fi

if [[ "${expectation_regressions}" != "0" ]]; then
  echo "planner-superiority gate failed: expectation_regressions=${expectation_regressions}" >&2
  exit 1
fi

if (( improvements < MIN_IMPROVEMENTS )); then
  echo "planner-superiority gate failed: improvements=${improvements}, required=${MIN_IMPROVEMENTS}" >&2
  exit 1
fi

echo "==> Planner-superiority gate passed"
echo "artifact_dir: ${ARTIFACT_DIR}"
