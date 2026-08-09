#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/coding_agent_v1_foundation_manifest.sh"

check_paths() {
  local missing=0
  for path in "$@"; do
    if [[ ! -e "${REPO_ROOT}/${path}" ]]; then
      echo "missing milestone path: ${path}" >&2
      missing=1
    fi
  done
  return "${missing}"
}

print_git_add() {
  local label="$1"
  local message="$2"
  shift 2
  local -a paths=("$@")

  echo "${label}"
  echo "commit message: ${message}"
  echo "git add -- \\"
  for i in "${!paths[@]}"; do
    local suffix=" \\"
    if [[ "${i}" -eq "$((${#paths[@]} - 1))" ]]; then
      suffix=""
    fi
    printf "  %s%s\n" "${paths[$i]}" "${suffix}"
  done
  echo
}

check_paths \
  "${foundation_commit_1_paths[@]}" \
  "${foundation_commit_2_paths[@]}" \
  "${foundation_commit_3_paths[@]}" \
  "${foundation_commit_4_paths[@]}"

echo "Run these from ${REPO_ROOT}:"
echo

print_git_add \
  "Commit 1: Framing And Current Status" \
  "${foundation_commit_1_message}" \
  "${foundation_commit_1_paths[@]}"

print_git_add \
  "Commit 2: Implementation Mapping And Portfolio Direction" \
  "${foundation_commit_2_message}" \
  "${foundation_commit_2_paths[@]}"

print_git_add \
  "Commit 3: Working V1 Harness" \
  "${foundation_commit_3_message}" \
  "${foundation_commit_3_paths[@]}"

print_git_add \
  "Commit 4: Milestone Packaging And Release Helpers" \
  "${foundation_commit_4_message}" \
  "${foundation_commit_4_paths[@]}"
