#!/usr/bin/env bash
set -euo pipefail

python3 -m qwen3_parity.prefix_logits_parity "$@"
