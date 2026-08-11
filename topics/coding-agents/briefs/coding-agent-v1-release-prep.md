# Coding Agent V1 Release Prep

This file turns the first coding-agent milestone into an execution checklist.

It answers:

what exactly should go into the first git-visible coding-agent milestone, and how should we verify it before publishing?

## Target Milestone

- `coding-agent-v1-foundation`

Related references:

- `projects/coding-agent-v1-first-milestone-checklist.md`
- `projects/coding-agent-git-launch-plan.md`
- `projects/coding-agent-current-status.md`
- `projects/coding-agent-v1-commit-stack-plan.md`

## Current Repo Reality

As of Sunday, August 9, 2026:

- `sebastian-llms` is already a git repository
- the worktree is still effectively in a pre-initial-publication state with broad untracked content
- `projects/coding-agent-v1/` is the main implementation artifact for the coding-agent lane
- the verified local test status for `coding-agent-v1` is `123 passed`

That means the immediate goal is not more theory.

The immediate goal is to package the first coding-agent artifact cleanly.

## Exact Artifact Set For The First Milestone

The first milestone should include these items.

### Core Framing

- `README.md`
- `projects/coding-agent-current-status.md`
- `projects/coding-agent-git-launch-plan.md`
- `projects/coding-agent-v1-first-milestone-checklist.md`
- `projects/coding-agent-v1-release-prep.md`

### Architecture And Planning

- `projects/coding-agent-from-scratch-implementation-map.md`
- `projects/coding-agent-portfolio-roadmap.md`
- `projects/coding-agent-flagship-capstone.md`
- `projects/coding-agent-v1-gap-analysis.md`

### External Reference

- `sources/external/building-a-coding-agent-from-scratch-course/README.md`

### Main Implementation

- `projects/coding-agent-v1/`

This is the minimum coherent set that tells the whole story:

- what the topic is
- what we learned from the PDF
- how the external repo influenced the implementation
- what is already built locally
- how the artifact should evolve next

Preferred staging-preview command:

```bash
/home/manishmehta/ui-projects/sebastian-llms/scripts/print_coding_agent_v1_foundation_git_add.sh
```

That helper validates the milestone paths and prints the exact `git add` command without staging anything automatically.

Preferred commit-stack preview command:

```bash
/home/manishmehta/ui-projects/sebastian-llms/scripts/print_coding_agent_v1_foundation_commit_stack.sh
```

That helper prints the exact `git add` command and commit message for each recommended milestone commit.

Preferred full publish-sequence preview command:

```bash
/home/manishmehta/ui-projects/sebastian-llms/scripts/print_coding_agent_v1_foundation_publish_sequence.sh
```

That helper prints the full ordered command flow for verification, staging, commit creation, and final log review.

Both helpers source:

- `scripts/coding_agent_v1_foundation_manifest.sh`

so the milestone path list and commit groups stay aligned.

## What Does Not Need To Be In The First Milestone

Do not block the milestone on cleaning or publishing every other lane in the repo, including:

- unrelated PDFs at the repo root
- non-coding-agent research tracks
- future Qwen3 work
- future architecture-advances work
- future benchmark expansion beyond current V1 evidence

Those can be organized in later milestones.

## Pre-Publish Verification Commands

Before treating the milestone as ready, rerun the most important verification commands from the `coding-agent-v1` workspace.

Preferred one-command path:

```bash
/home/manishmehta/ui-projects/sebastian-llms/projects/coding-agent-v1/scripts/verify_foundation_release.sh
```

Equivalent manual commands:

```bash
cd /home/manishmehta/ui-projects/sebastian-llms/projects/coding-agent-v1
python3 -m pytest tests/test_agent_loop.py -q
python3 -m pytest tests/test_eval_harness.py -q
python3 -m pytest tests -q
```

Expected current outcome baseline:

- focused `test_agent_loop` suite passes
- focused `test_eval_harness` suite passes
- full `tests` suite passes
- last known full-suite result: `123 passed`

## Pre-Publish Readability Checks

Before publishing, quickly inspect these files for clarity and consistency:

- `README.md`
- `projects/coding-agent-current-status.md`
- `projects/coding-agent-git-launch-plan.md`
- `projects/coding-agent-v1-first-milestone-checklist.md`
- `projects/coding-agent-v1/README.md`

The reviewer should be able to understand within a few minutes:

- what the coding-agent lane is
- why the external course repo matters
- what `coding-agent-v1` can do today
- what is intentionally left for later

## Suggested Commit Shape

If we want a clean first milestone history, the safest sequence is:

1. framing and roadmap docs
2. implementation-map and external-reference docs
3. `coding-agent-v1` implementation
4. milestone and release-prep docs

If we prefer a single first milestone commit, this document still defines what that one commit must contain.

For the exact commit grouping and messages, see:

- `projects/coding-agent-v1-commit-stack-plan.md`

## Suggested Commit Message Options

If the first milestone is one commit:

- `Introduce coding-agent-v1 foundation milestone`

If the first milestone is a short commit stack:

- `Frame coding-agent portfolio and current status`
- `Map coding-agent theory to implementation structure`
- `Add coding-agent-v1 foundation harness`
- `Document first coding-agent milestone packaging`

## Reviewer Checklist

Before calling the milestone done, confirm these reviewer-facing statements are true:

- this repo contains a real coding-agent implementation
- the implementation is not just a prompt wrapper
- the harness has bounded tools and permissions
- the harness has session and eval discipline
- the repo documents both current capability and current limits

## Next Action After This Prep

After this prep doc, the next concrete action should be one of:

1. assemble the actual first milestone commit set
2. rerun the `coding-agent-v1` verification commands immediately before commit
3. tighten any remaining README wording that weakens the reviewer story

## Bottom Line

The first milestone is already conceptually ready.

This prep doc exists to make the publication step mechanical:

include the right files, rerun the right tests, and publish `coding-agent-v1` as the first serious coding-agent artifact in the repo.
