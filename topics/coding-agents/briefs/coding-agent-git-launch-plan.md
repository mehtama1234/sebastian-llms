# Coding Agent Git Launch Plan

This file explains how to present the coding-agent work in this repo as a clean git-visible project story.

## Purpose

We already have:

- source notes from `CodingAgents.pdf`
- an external implementation reference in `sources/external/building-a-coding-agent-from-scratch-course/`
- a working local harness in `projects/coding-agent-v1/`

What is still needed is a clear answer to:

what goes into git first, and what should each visible artifact prove?

This file answers that.

## The Main Story We Should Tell

The best git story is not:

- "here are random notes"
- "here is one giant unfinished agent"

The best git story is:

1. we understood the architecture
2. we mapped theory to implementation structure
3. we built a working V1 harness
4. we measured it with repeatable evals
5. we kept evolving it toward a flagship coding agent

That sequence is easier for other people to review and easier for us to maintain.

## What The Current Repo Already Has

As of Sunday, August 9, 2026, the coding-agent track already has five strong assets:

1. `projects/coding-agent-current-status.md`
2. `projects/coding-agent-from-scratch-implementation-map.md`
3. `projects/coding-agent-portfolio-roadmap.md`
4. `projects/coding-agent-flagship-capstone.md`
5. `projects/coding-agent-v1/`

The fifth item is the most important because it is implemented code with a passing local test suite:

- `123 passed`

So the git plan should treat `coding-agent-v1` as the main artifact, and the docs as supporting architecture and roadmap context.

## Recommended Git Structure

The coding-agent work should read as one connected lane inside the repo:

- `README.md`: high-level entry point
- `projects/coding-agent-current-status.md`: plain-language explanation
- `projects/coding-agent-v1-first-milestone-checklist.md`: definition of the first git-ready implementation milestone
- `projects/coding-agent-v1-release-prep.md`: exact artifact set and verification steps for publication
- `projects/coding-agent-v1-commit-stack-plan.md`: exact commit grouping for a clean first milestone history
- `projects/coding-agent-portfolio-roadmap.md`: multi-project learning path
- `projects/coding-agent-flagship-capstone.md`: serious end-state target
- `projects/coding-agent-from-scratch-implementation-map.md`: bridge from PDF ideas to practical module structure
- `projects/coding-agent-v1/`: active implementation
- `sources/external/building-a-coding-agent-from-scratch-course/README.md`: tracked external reference

That is enough structure for a reviewer to understand both:

- why the project exists
- what is already working

## What To Put In Git First

If we want a clean public or semi-public history, the best first wave is:

### 1. Repo Framing Commit

This commit should establish:

- the repo purpose
- the coding-agent topic as a flagship track
- the plain-language status doc

The goal of this commit is simple orientation.

### 2. Research-To-Implementation Mapping Commit

This commit should include:

- `projects/coding-agent-from-scratch-implementation-map.md`
- the tracked external course reference
- any cleaned note showing how `CodingAgents.pdf` maps to real system parts

The goal here is to prove we are not building blindly.

### 3. Working V1 Harness Commit

This is the first major implementation commit or commit stack.

It should center on:

- `projects/coding-agent-v1/`

and should show:

- repo-aware context gathering
- bounded tools
- permission gating
- session state
- validation behavior

The goal is to make the first working agent harness visible.

### 4. Task-Class Expansion Commit

This commit should make it clear that the agent handles more than one happy path.

It should highlight support for:

- fix
- feature
- rename
- diagnose
- resume

The goal is breadth across minimum coding-agent task classes.

### 5. Eval And Regression Discipline Commit

This commit should show that the harness is measurable.

It should include visible evidence for:

- fixed eval scenarios
- saved eval artifacts
- baseline comparison
- guarded promotion or regression checks

This is the point where the project starts to look serious instead of demo-only.

## What Each Artifact Should Demonstrate

Each major visible artifact should answer one specific question.

### `coding-agent-current-status.md`

Question answered:

- what are we doing here in simple words?

### `coding-agent-from-scratch-implementation-map.md`

Question answered:

- how did we translate the PDF into implementation structure?

### `coding-agent-portfolio-roadmap.md`

Question answered:

- what is the larger portfolio path beyond V1?

### `coding-agent-flagship-capstone.md`

Question answered:

- what does success look like at the full-system level?

### `coding-agent-v1/`

Question answered:

- can we actually build a working coding-agent harness?

## What Reviewers Should Be Able To See Quickly

A reviewer landing in the repo should be able to learn these facts quickly:

- this repo studies coding agents seriously
- the PDF is being used as architecture guidance
- the external Decoding AI course repo is being used as a practical implementation reference
- there is already a working local harness
- the harness is tested
- the work is evolving toward a bigger flagship system

If a reviewer cannot tell those things within a few minutes, the repo presentation is too weak.

## Recommended Near-Term Git Milestones

The next good milestones for the coding-agent lane are:

1. stabilize the current V1 implementation and its docs
2. add stronger planner quality inside `coding-agent-v1`
3. improve memory and resume quality
4. expand eval scenarios across each minimum task class
5. package examples and saved artifacts for review

Those are better milestones than adding random features because each one strengthens the core thesis of the project.

## What Not To Do

Avoid these mistakes:

- dumping notes without showing implementation
- publishing only code without explaining the architecture
- presenting one happy-path demo as if it proves agent quality
- adding advanced features before the single-agent loop is stable
- making the git history about experiments instead of milestones

## Bottom Line

The right git story for this topic is:

research understanding -> implementation mapping -> working V1 harness -> measured progress -> stronger flagship agent

That is the cleanest way to show depth on coding agents in this repo.
