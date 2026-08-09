#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_DIR}"

required_files=(
  "README.md"
  "pyproject.toml"
  "tests/test_agent_loop.py"
  "tests/test_eval_harness.py"
)

for path in "${required_files[@]}"; do
  if [[ ! -f "${path}" ]]; then
    echo "missing required file: ${path}" >&2
    exit 1
  fi
done

echo "==> Running focused agent loop tests"
python3 -m pytest tests/test_agent_loop.py -q

echo "==> Running focused eval harness tests"
python3 -m pytest tests/test_eval_harness.py -q

echo "==> Running full coding-agent-v1 test suite"
python3 -m pytest tests -q

echo "==> coding-agent-v1 foundation verification passed"
