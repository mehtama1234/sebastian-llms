#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOPICS_DIR="$(cd "$ROOT_DIR/../.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
MANIFEST_PATH="$TOPICS_DIR/llm-developments-2026/evals/datasets/real-repos/sample-benchmark.json"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src:$TOPICS_DIR/llm-developments-2026/code/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.real_indexer_vs_attention \
  --manifest "$MANIFEST_PATH" \
  --artifact-json "$ROOT_DIR/artifacts/long_context/real_indexer_vs_attention.json" \
  --artifact-md "$ROOT_DIR/artifacts/long_context/real_indexer_vs_attention.md" \
  --stdout
