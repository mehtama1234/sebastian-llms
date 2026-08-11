#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/coding_agent_v1_foundation_manifest.sh"

print_commit_sequence() {
  local label="$1"
  local message="$2"
  shift 2
  local -a paths=("$@")

  echo "${label}"
  echo "git add -- \\"
  for i in "${!paths[@]}"; do
    local suffix=" \\"
    if [[ "${i}" -eq "$((${#paths[@]} - 1))" ]]; then
      suffix=""
    fi
    printf "  %s%s\n" "${paths[$i]}" "${suffix}"
  done
  echo "git diff --cached --stat"
  echo "git commit -m \"${message}\""
  echo
}

echo "Run these from ${REPO_ROOT}:"
echo
echo "# 1. Verify the milestone"
echo "./projects/coding-agent-v1/scripts/verify_foundation_release.sh"
echo
echo "# 2. Preview the full milestone staging set"
echo "./scripts/print_coding_agent_v1_foundation_git_add.sh"
echo
echo "# 3. Preview the commit groups"
echo "./scripts/print_coding_agent_v1_foundation_commit_stack.sh"
echo
echo "# 4. Create the four recommended commits"
echo

print_commit_sequence \
  "Commit 1: Framing And Current Status" \
  "${foundation_commit_1_message}" \
  "${foundation_commit_1_paths[@]}"

print_commit_sequence \
  "Commit 2: Implementation Mapping And Portfolio Direction" \
  "${foundation_commit_2_message}" \
  "${foundation_commit_2_paths[@]}"

print_commit_sequence \
  "Commit 3: Working V1 Harness" \
  "${foundation_commit_3_message}" \
  "${foundation_commit_3_paths[@]}"

print_commit_sequence \
  "Commit 4: Milestone Packaging And Release Helpers" \
  "${foundation_commit_4_message}" \
  "${foundation_commit_4_paths[@]}"

echo "# 5. Review the result"
echo "git log --oneline --decorate -n 4"
