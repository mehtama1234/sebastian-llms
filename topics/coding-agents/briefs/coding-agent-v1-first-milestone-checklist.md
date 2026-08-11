# Coding Agent V1 First Milestone Checklist

This file defines the first git-ready milestone for the coding-agent work in this repo.

It is meant to answer one practical question:

when do we treat `projects/coding-agent-v1/` as the first serious published coding-agent artifact?

## Milestone Name

`coding-agent-v1-foundation`

## Milestone Goal

Package `projects/coding-agent-v1/` as the first serious implementation artifact in the repo, with enough documentation and verification that a reviewer can understand what it does, what it does not do yet, and why it matters.

## Why This Is The Right First Milestone

This is the right first milestone because `coding-agent-v1` already proves the core thesis of the coding-agent topic:

- the system around the model matters
- a coding agent needs repo awareness, tools, permissions, memory, and validation
- we can already implement that as a bounded local harness

As of Sunday, August 9, 2026, this harness is not theoretical.

Its local test suite is passing with:

- `123 passed`

## What This Milestone Should Demonstrate

When this milestone is ready, a reviewer should be able to see that the repo already contains a real coding-agent foundation with:

- repo-aware context gathering
- bounded file/search/edit/command tools
- permission gating
- task-flow selection
- validation after edits
- saved session state
- eval artifacts and comparison support

## Required Conditions

Treat the milestone as ready only if all of these conditions are true.

### 1. Project Framing Is Clear

Required:

- the top-level repo README points to the coding-agent lane
- the plain-language status doc exists
- the git launch plan exists

Current evidence:

- `README.md`
- `projects/coding-agent-current-status.md`
- `projects/coding-agent-git-launch-plan.md`
- `projects/coding-agent-v1-release-prep.md`

Status:

- `ready`

### 2. The External Reference Is Tracked

Required:

- the Decoding AI from-scratch course repo is represented as a tracked reference
- the repo explains why that external source matters

Current evidence:

- `sources/external/building-a-coding-agent-from-scratch-course/README.md`
- `projects/coding-agent-from-scratch-implementation-map.md`

Status:

- `ready`

### 3. The Working Harness Exists

Required:

- the repo contains an actual implementation folder, not just notes
- the implementation has a clear README

Current evidence:

- `projects/coding-agent-v1/`
- `projects/coding-agent-v1/README.md`

Status:

- `ready`

### 4. The Harness Covers Minimum V1 Behaviors

Required:

- inspect behavior
- fix behavior
- feature behavior
- rename behavior
- diagnose behavior
- session review or resume behavior

Current evidence:

- described in `projects/coding-agent-v1/README.md`
- covered by the implementation and current test suite

Status:

- `ready`

### 5. Safety Boundaries Are Present

Required:

- workspace path boundaries
- allow/ask/deny permission behavior
- bounded command execution

Current evidence:

- described in `projects/coding-agent-v1/README.md`
- reflected in the current harness design and tests

Status:

- `ready`

### 6. Validation And Eval Discipline Exist

Required:

- validation reruns after edits
- fixed eval scenarios
- saved eval artifacts
- comparison or baseline support

Current evidence:

- described in `projects/coding-agent-v1/README.md`
- evaluated in the current harness and tests

Status:

- `ready`

### 7. Current Limitations Are Honest

Required:

- the repo should state what V1 does not do yet
- the next steps should be visible

Current evidence:

- `projects/coding-agent-v1/README.md`
- `projects/coding-agent-v1-gap-analysis.md`
- `projects/coding-agent-flagship-capstone.md`

Status:

- `ready`

## What Does Not Need To Be Finished For This Milestone

Do not block this milestone on:

- full LLM integration
- advanced subagent support
- sandbox backends
- perfect long-session memory
- broad benchmark-scale eval coverage

Those are important later, but they are not required for the first serious foundation milestone.

## What Should Be Included In The Milestone Commit Or Commit Stack

The milestone should include:

- the coding-agent framing docs
- the external implementation reference note
- the `coding-agent-v1` implementation
- test-backed evidence that the harness is working

In practice, the most important visible proof is:

- `projects/coding-agent-v1/`
- its README
- the current passing test state

For the exact publish package and verification commands, see:

- `projects/coding-agent-v1-release-prep.md`
- `projects/coding-agent-v1/scripts/verify_foundation_release.sh`

## Reviewer Outcome

If this milestone is packaged well, a reviewer should be able to say:

- this repo has a real coding-agent implementation
- it is more than a note-taking project
- it already demonstrates the basic harness shape
- it is set up to evolve into a stronger flagship coding agent

## Next Milestone After This One

The best next milestone after `coding-agent-v1-foundation` is:

`coding-agent-v1-planner-and-eval-upgrade`

That next milestone should focus on:

- stronger planner quality
- broader validation selection
- broader eval coverage across the minimum task classes

## Bottom Line

The first milestone should not wait for the perfect agent.

It should package the current reality clearly:

we already have a working V1 coding-agent foundation, and it is strong enough to be the first serious git-visible artifact.
