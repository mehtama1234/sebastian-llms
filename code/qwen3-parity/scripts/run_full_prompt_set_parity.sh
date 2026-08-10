#!/usr/bin/env bash
set -euo pipefail

python3 -m qwen3_parity.full_prompt_set_parity "$@"
