#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
BENCHMARK_MODE="proxy_numeric"
OBJECTIVE="balanced"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --benchmark-mode)
      if [[ $# -lt 2 ]]; then
        echo "missing value for --benchmark-mode" >&2
        exit 1
      fi
      BENCHMARK_MODE="$2"
      shift 2
      ;;
    --objective)
      if [[ $# -lt 2 ]]; then
        echo "missing value for --objective" >&2
        exit 1
      fi
      OBJECTIVE="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

case "$BENCHMARK_MODE" in
  proxy_numeric|torch_proxy|summary_only)
    ;;
  *)
    echo "unsupported benchmark mode: $BENCHMARK_MODE" >&2
    exit 1
    ;;
esac

case "$OBJECTIVE" in
  memory|speed|balanced)
    ;;
  *)
    echo "unsupported objective: $OBJECTIVE" >&2
    exit 1
    ;;
esac

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

PLAN_ARTIFACT="$ROOT_DIR/artifacts/plans/qwen3-${OBJECTIVE}-run-plan.json"
if [[ "$BENCHMARK_MODE" != "proxy_numeric" ]]; then
  PLAN_ARTIFACT="$ROOT_DIR/artifacts/plans/qwen3-${OBJECTIVE}-${BENCHMARK_MODE}-run-plan.json"
fi

"$VENV_PYTHON" -m arch_adv_2026.long_context_plan \
  --selector-artifact "$ROOT_DIR/artifacts/long_context/qwen3_long_context_medium_selector.json" \
  --config-family "qwen3" \
  --objective "$OBJECTIVE" \
  --benchmark-mode "$BENCHMARK_MODE" \
  --root-dir "$ROOT_DIR" \
  --artifact-out "$PLAN_ARTIFACT" \
  --stdout
