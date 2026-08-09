#!/usr/bin/env bash

# Shared manifest for the coding-agent-v1 foundation milestone.
# Other helper scripts source this file so the artifact list and commit groups
# stay in one place.

foundation_all_paths=(
  "README.md"
  ".gitignore"
  "projects/coding-agent-current-status.md"
  "projects/coding-agent-git-launch-plan.md"
  "projects/coding-agent-v1-first-milestone-checklist.md"
  "projects/coding-agent-v1-release-prep.md"
  "projects/coding-agent-v1-commit-stack-plan.md"
  "projects/coding-agent-from-scratch-implementation-map.md"
  "projects/coding-agent-portfolio-roadmap.md"
  "projects/coding-agent-flagship-capstone.md"
  "projects/coding-agent-v1-gap-analysis.md"
  "sources/external/building-a-coding-agent-from-scratch-course/README.md"
  "projects/coding-agent-v1"
  "projects/coding-agent-v1/scripts/verify_foundation_release.sh"
  "scripts/coding_agent_v1_foundation_manifest.sh"
  "scripts/print_coding_agent_v1_foundation_git_add.sh"
  "scripts/print_coding_agent_v1_foundation_commit_stack.sh"
)

foundation_commit_1_message="Frame coding-agent track and current status"
foundation_commit_1_paths=(
  "README.md"
  "projects/coding-agent-current-status.md"
)

foundation_commit_2_message="Map coding-agent theory to implementation structure"
foundation_commit_2_paths=(
  "projects/coding-agent-from-scratch-implementation-map.md"
  "projects/coding-agent-portfolio-roadmap.md"
  "projects/coding-agent-flagship-capstone.md"
  "sources/external/building-a-coding-agent-from-scratch-course/README.md"
)

foundation_commit_3_message="Add coding-agent-v1 foundation harness"
foundation_commit_3_paths=(
  "projects/coding-agent-v1"
)

foundation_commit_4_message="Document coding-agent-v1 milestone packaging"
foundation_commit_4_paths=(
  ".gitignore"
  "projects/coding-agent-git-launch-plan.md"
  "projects/coding-agent-v1-gap-analysis.md"
  "projects/coding-agent-v1-first-milestone-checklist.md"
  "projects/coding-agent-v1-release-prep.md"
  "projects/coding-agent-v1-commit-stack-plan.md"
  "scripts/coding_agent_v1_foundation_manifest.sh"
  "scripts/print_coding_agent_v1_foundation_git_add.sh"
  "scripts/print_coding_agent_v1_foundation_commit_stack.sh"
  "scripts/print_coding_agent_v1_foundation_publish_sequence.sh"
)
