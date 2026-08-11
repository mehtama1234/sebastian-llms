#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 -m qwen3_parity.compare_configs \
  --reference "$ROOT_DIR/artifacts/reference/qwen3_0_6b_reference_snapshot.json" \
  --scratch "$ROOT_DIR/artifacts/scratch/qwen3_0_6b_scratch_config.json"
