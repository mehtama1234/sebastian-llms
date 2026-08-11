#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 -m qwen3_parity.reference.inspect \
  --config-only \
  --artifact-dir "$ROOT_DIR/artifacts/reference" \
  --stdout
