#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
OBJECTIVE="quality_preserving_memory"
EXECUTION_MODE="focused_proxy_compare"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --objective)
      if [[ $# -lt 2 ]]; then
        echo "missing value for --objective" >&2
        exit 1
      fi
      OBJECTIVE="$2"
      shift 2
      ;;
    --execution-mode)
      if [[ $# -lt 2 ]]; then
        echo "missing value for --execution-mode" >&2
        exit 1
      fi
      EXECUTION_MODE="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

SUFFIX=""
if [[ "$EXECUTION_MODE" != "focused_proxy_compare" ]]; then
  SUFFIX="-$EXECUTION_MODE"
fi

"$VENV_PYTHON" -m arch_adv_2026.long_context_variant_execute \
  --plan-artifact "$ROOT_DIR/artifacts/plans/qwen3-${OBJECTIVE}${SUFFIX}-variant-proxy-plan.json" \
  --artifact-out "$ROOT_DIR/artifacts/plans/qwen3-${OBJECTIVE}${SUFFIX}-variant-proxy-execution.json" \
  --stdout
