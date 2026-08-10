#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 -m qwen3_parity.scratch.config_snapshot \
  --artifact-dir "$ROOT_DIR/artifacts/scratch" \
  --stdout
