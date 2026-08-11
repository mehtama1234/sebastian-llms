#!/usr/bin/env bash
set -euo pipefail

python3 -m qwen3_parity.layer0_forward_parity "$@"
