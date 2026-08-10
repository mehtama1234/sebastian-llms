#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# The final memo depends on every refreshed decision-layer artifact, so the
# standalone memo entrypoint delegates to the full decision-stack refresh path.
bash "$ROOT_DIR/scripts/run_decision_stack.sh"
