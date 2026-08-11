# Coding Agent V1 Commit Stack Plan

This file defines the cleanest commit stack for publishing the first coding-agent milestone.

It answers:

if we do not want one giant commit, how should we split `coding-agent-v1-foundation` into a small, reviewable history?

## Target Milestone

- `coding-agent-v1-foundation`

Related references:

- `projects/coding-agent-v1-release-prep.md`
- `projects/coding-agent-v1-first-milestone-checklist.md`
- `scripts/coding_agent_v1_foundation_manifest.sh`
- `scripts/print_coding_agent_v1_foundation_git_add.sh`
- `scripts/print_coding_agent_v1_foundation_commit_stack.sh`
- `scripts/print_coding_agent_v1_foundation_publish_sequence.sh`

## Why A Commit Stack Is Better Here

For this repo, a short commit stack is better than one large commit because the coding-agent lane already contains three distinct kinds of work:

- framing and portfolio explanation
- research-to-implementation mapping
- the actual local harness implementation

If those are mixed together in one large first commit, the repo story becomes harder to review.

## Recommended Four-Commit Stack

The cleanest first milestone stack is:

1. framing and current-status docs
2. implementation mapping and portfolio direction
3. `coding-agent-v1` implementation
4. milestone packaging and release helpers

That sequence matches the repo story we want a reviewer to follow.

## Commit 1: Framing And Current Status

Purpose:

- explain what this repo is doing in simple words
- establish coding agents as a flagship lane

Recommended files:

- `README.md`
- `projects/coding-agent-current-status.md`

Recommended message:

- `Frame coding-agent track and current status`

Reviewer takeaway:

- this repo has a serious coding-agent lane
- there is already a working implementation direction, not just random notes

## Commit 2: Implementation Mapping And Portfolio Direction

Purpose:

- show how the PDF ideas map to actual implementation structure
- show the bigger project sequence beyond V1

Recommended files:

- `projects/coding-agent-from-scratch-implementation-map.md`
- `projects/coding-agent-portfolio-roadmap.md`
- `projects/coding-agent-flagship-capstone.md`
- `sources/external/building-a-coding-agent-from-scratch-course/README.md`

Recommended message:

- `Map coding-agent theory to implementation structure`

Reviewer takeaway:

- the work is grounded in both source material and an external implementation reference
- there is a coherent portfolio path, not just one isolated build

## Commit 3: Working V1 Harness

Purpose:

- publish the actual local coding-agent implementation
- make the core artifact visible as code, tests, and README

Recommended files:

- `projects/coding-agent-v1/`

Recommended message:

- `Add coding-agent-v1 foundation harness`

Reviewer takeaway:

- the repo contains a real coding-agent implementation
- the project is test-backed and repo-aware

## Commit 4: Milestone Packaging And Release Helpers

Purpose:

- make the milestone operational, reviewable, and repeatable
- define the milestone criteria and release path

Recommended files:

- `.gitignore`
- `projects/coding-agent-git-launch-plan.md`
- `projects/coding-agent-v1-gap-analysis.md`
- `projects/coding-agent-v1-first-milestone-checklist.md`
- `projects/coding-agent-v1-release-prep.md`
- `projects/coding-agent-v1-commit-stack-plan.md`
- `scripts/coding_agent_v1_foundation_manifest.sh`
- `scripts/print_coding_agent_v1_foundation_git_add.sh`
- `scripts/print_coding_agent_v1_foundation_commit_stack.sh`
- `scripts/print_coding_agent_v1_foundation_publish_sequence.sh`

Recommended message:

- `Document coding-agent-v1 milestone packaging`

Reviewer takeaway:

- the first milestone is not just code
- the repo has a clear verification path and a clear publication path

## If One Commit Is Preferred Instead

If the first milestone must be collapsed into a single commit, use:

- `Introduce coding-agent-v1 foundation milestone`

That is acceptable, but it is weaker as a review story than the four-commit stack above.

## Suggested Order Of Operations

If we publish with the four-commit stack, the safest flow is:

1. rerun `projects/coding-agent-v1/scripts/verify_foundation_release.sh`
2. use `scripts/print_coding_agent_v1_foundation_git_add.sh` to confirm the full artifact set
3. use `scripts/print_coding_agent_v1_foundation_commit_stack.sh` to print the exact staging command for each commit
4. split the paths into the four groups above
5. review `git diff --cached` before each commit
6. create the commits in the order defined here

## What Not To Do

Avoid:

- mixing unrelated research tracks into these commits
- committing repo caches or build artifacts
- putting milestone docs before the implementation they describe
- inventing a more complicated history than the repo needs

## Bottom Line

The cleanest first milestone history is:

frame the lane -> map the implementation approach -> publish the harness -> document the release path

That gives `coding-agent-v1-foundation` a readable, defensible git story.
