#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/coding_agent_v1_foundation_manifest.sh"

missing=0

for path in "${foundation_all_paths[@]}"; do
  if [[ ! -e "${REPO_ROOT}/${path}" ]]; then
    echo "missing milestone path: ${path}" >&2
    missing=1
  fi
done

if [[ "${missing}" -ne 0 ]]; then
  exit 1
fi

echo "Run this from ${REPO_ROOT}:"
echo
echo "git add -- \\"
for i in "${!foundation_all_paths[@]}"; do
  suffix=" \\"
  if [[ "${i}" -eq "$((${#foundation_all_paths[@]} - 1))" ]]; then
    suffix=""
  fi
  printf "  %s%s\n" "${foundation_all_paths[$i]}" "${suffix}"
done
