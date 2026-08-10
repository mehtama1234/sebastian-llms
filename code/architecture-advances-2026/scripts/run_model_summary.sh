#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

python3 -m arch_adv_2026.cli \
  --config "$ROOT_DIR/configs/tiny-baseline.json" \
  --artifact "$ROOT_DIR/artifacts/summaries/tiny-baseline.json" \
  --stdout

python3 -m arch_adv_2026.cli \
  --config "$ROOT_DIR/configs/tiny-kv-sharing.json" \
  --artifact "$ROOT_DIR/artifacts/summaries/tiny-kv-sharing.json" \
  --stdout
