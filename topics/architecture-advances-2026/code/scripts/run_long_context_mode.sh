#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLAN_SCRIPT="$ROOT_DIR/scripts/run_long_context_plan.sh"
EXECUTE_SCRIPT="$ROOT_DIR/scripts/run_long_context_execute.sh"
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

"$PLAN_SCRIPT" --benchmark-mode "$BENCHMARK_MODE" --objective "$OBJECTIVE"
"$EXECUTE_SCRIPT" --benchmark-mode "$BENCHMARK_MODE" --objective "$OBJECTIVE"
