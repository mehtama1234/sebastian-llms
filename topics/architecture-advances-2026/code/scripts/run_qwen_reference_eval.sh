#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT_DIR/../.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.hf_eval \
  --model-id "Qwen/Qwen3-0.6B" \
  --cases "$REPO_ROOT/evals/architecture-advances-2026/qwen-reference-prompts.jsonl" \
  --artifact "$ROOT_DIR/artifacts/reference/qwen3_0_6b_eval.json" \
  --stdout
