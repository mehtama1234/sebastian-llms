#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 -m qwen3_parity.weight_map --artifact-dir "$ROOT_DIR/artifacts/mapping" --stdout
