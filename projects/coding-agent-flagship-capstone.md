# Coding Agent Flagship Capstone

## Purpose

This brief defines the strongest end-to-end project to build in this repo around coding agents.

It is the project that should tie together:

- `CodingAgents.pdf`
- the Decoding AI from-scratch course repo
- our local `coding-agent-v1` implementation work

This is not meant to replace `v1-build-plan.md`.

It is meant to state the bigger target that the smaller projects are building toward.

## One-Sentence Goal

Build a repo-aware coding agent that can take a real software task from request to verified patch with bounded tools, approval rules, resumable session state, and regression-aware evaluation.

## In Simple Words

The agent should be able to:

- understand the codebase it is working in
- inspect the right files and commands
- make targeted code changes
- run tests or validation
- recover from failures
- explain what it changed
- leave behind logs and artifacts that make the work reviewable

If it can only chat, or only edit once, or only run one command, that is not enough.

The goal is to build a coding system, not just a coding prompt.

## What This Project Should Teach

This capstone should teach five things clearly.

### 1. The Model Is Only One Layer

The real coding agent is the combination of:

- model
- agent loop
- tool layer
- permission layer
- memory layer
- validation layer
- eval layer

That is the main systems lesson in this topic.

### 2. Safety Is Part Of Product Quality

Useful coding agents need:

- path boundaries
- approval gates
- bounded shell execution
- explicit failure handling

Without those constraints, the system is not serious enough for real repo work.

### 3. Memory And Context Quality Matter

The agent needs enough state to continue work across steps and sessions without flooding itself with raw logs.

That means:

- workspace summary
- short working memory
- transcript persistence
- context compaction over time

### 4. Validation Matters More Than Demos

The project should make it normal to ask:

- did the tests pass
- did the change regress another scenario
- does the current run beat the baseline

The system should not rely on one good-looking example.

### 5. Coding Agents Are Productizable

The capstone should show how research ideas become a usable engineering tool with:

- CLI or interface surface
- persistent artifacts
- reproducible task flows
- repo-friendly outputs

## Required Capabilities

The capstone should include all of the following.

### Core Task Loop

- accept a coding task
- inspect workspace context before acting
- choose and invoke bounded tools
- apply targeted changes
- run validation
- produce a final result summary

### Repo Awareness

- detect repo root
- summarize important files and structure
- read project instructions such as `README.md`
- avoid acting on invented paths

### Tool Layer

- file read
- code search
- targeted edit
- bounded shell command
- approval request for risky actions

### Safety Layer

- workspace path restrictions
- allow/ask/deny permission decisions
- command limits and output clipping
- explicit handling for denied actions

### Session Layer

- durable session transcript
- reviewable event log
- resume/review flow
- compact working summary

### Evaluation Layer

- fixed task scenarios
- saved eval artifacts
- baseline comparison
- regression detection
- promotion discipline for better runs

## Minimum Task Set

A serious capstone should prove itself on more than one kind of task.

Minimum task classes:

1. failing-test repair
2. small feature edit
3. safe multi-file rename
4. failure diagnosis without editing
5. resume and continue a prior session

## Concrete Success Criteria

We should treat this project as successful only if all of these are true.

1. The agent can complete at least one real example in each minimum task class.
2. The agent can rerun validation after edits and report the result clearly.
3. The agent can stop safely when permission is denied or the task is out of scope.
4. The agent can save enough state for later review and continuation.
5. The agent can compare saved runs instead of relying on one-off demos.
6. The project includes written architecture notes explaining the harness decisions.

## Recommended Build Sequence

The cleanest path in this repo is:

1. use `projects/coding-agent-v1/` as the active implementation harness
2. finish the V1 task classes and session/eval discipline
3. add compaction and stronger working memory
4. add subagent support only after the single-agent loop is stable
5. add a real model-backed planner when the runtime boundaries are already clear

This keeps the build order aligned with both:

- `CodingAgents.pdf`
- `projects/coding-agent-from-scratch-implementation-map.md`
- `projects/coding-agent-v1-gap-analysis.md`

## What To Show In Git

When this becomes a stronger repo artifact, the best visible outputs are:

- one flagship implementation folder
- a clear README with supported task classes
- saved eval and decision artifacts
- example session logs
- short demos on real repository tasks
- architecture docs explaining why the harness is shaped this way

## Relationship To Current Work

As of Sunday, August 9, 2026, `projects/coding-agent-v1/` is already the strongest implementation anchor in this repo.

It already demonstrates:

- repo-aware context gathering
- file read/search/edit flows
- bounded command execution
- permission handling
- repair loop behavior
- session review and resume
- eval artifacts, baselines, comparison, and guarded auto-promotion

That means the next step is not to start over.

The next step is to keep pushing `coding-agent-v1` toward this fuller capstone target.

## Bottom Line

The end-to-end meaty goal on coding agents is not:

"build a bot that writes code once."

It is:

"build a bounded coding system that can inspect, change, validate, remember, and evaluate its own work inside a real repo."
