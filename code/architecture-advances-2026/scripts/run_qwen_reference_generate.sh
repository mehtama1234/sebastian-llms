#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "missing venv python at $VENV_PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$VENV_PYTHON" -m arch_adv_2026.hf_generate \
  --model-id "Qwen/Qwen3-0.6B" \
  --prompt-mode "chat" \
  --system-prompt "You are a concise technical assistant. Answer in English. Do not output chain-of-thought, reasoning traces, or <think> tags. Give only the final answer." \
  --prompt "Summarize why KV-cache reduction matters for long-context inference in two sentences." \
  --max-new-tokens 32 \
  --artifact "$ROOT_DIR/artifacts/reference/qwen3_0_6b_generation.json" \
  --stdout
