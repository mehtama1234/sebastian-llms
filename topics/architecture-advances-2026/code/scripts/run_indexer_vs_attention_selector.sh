#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

if [ ! -f "$ROOT_DIR/artifacts/long_context/indexer_vs_attention.json" ]; then
  "$ROOT_DIR/scripts/run_indexer_vs_attention.sh" >/dev/null
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.indexer_vs_attention_selector \
  --artifact "$ROOT_DIR/artifacts/long_context/indexer_vs_attention.json" \
  --selector-out "$ROOT_DIR/artifacts/long_context/indexer_vs_attention_selector.json" \
  --stdout
