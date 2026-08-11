# Coding Agent V1 Gap Analysis

## Purpose

This document maps the flagship coding-agent capstone requirements against the current state of `projects/coding-agent-v1/`.

The goal is to answer one practical question:

what is already done, what is partially done, and what should be built next to turn `coding-agent-v1` into the flagship capstone?

## Current Reference Point

As of Sunday, August 9, 2026:

- `projects/coding-agent-v1/` is the active implementation harness
- its local test suite is passing with `123 passed`
- it already demonstrates repo context, tools, permissions, repair flow, session review/resume, and eval artifact management

## Status Key

- `done`: implemented and already demonstrated in the repo
- `partial`: implemented in a narrower form, but not yet strong enough for the capstone target
- `next`: not yet built or not yet demonstrated clearly enough

## Capstone Requirement Map

### 1. Core Task Loop

Status: `partial`

What exists:

- request -> inspect -> act -> validate -> report loop
- explicit and natural-language task-flow routing for inspect, fix, feature, rename, and diagnose requests with scored planner selection informed by workspace structure and test evidence
- explicit task plans that persist flow choice, feature strategy, initial actions, validation command, and planning reasons
- task-aware validation selection that can narrow feature and rename flows to matching test files from request text or module-aware workspace evidence, including nested repo-relative test paths
- small feature edit flows for explicit or inferred argparse CLI flags, config-option defaults including inferred and natural-language option requests, and environment-variable-backed config entries including inferred and natural-language env-var requests
- repair flow for small failing-test cases
- safe multi-file rename flow
- diagnose-only flow that gathers failure evidence without applying edits

What is missing:

- a broader planner that chooses between task strategies more intelligently than the current scored evidence-based rules
- stronger support for non-test-driven tasks
- deeper validation heuristics beyond the current text-and-module matching rules

Best next build:

- replace the current scored evidence-based planner rules with a stronger planner that can choose among task strategies with better evidence

### 2. Repo Awareness

Status: `done`

What exists:

- repo-root detection
- workspace summary
- project instruction reading such as `README.md`
- bounded workspace behavior

Why this is effectively done for V1:

- this already supports the current harness behaviors and aligns with the capstone requirement

### 3. Tool Layer

Status: `partial`

What exists:

- file read
- code search
- targeted edit
- bounded shell command execution
- approval request behavior

What is missing:

- richer edit strategies for harder changes
- stronger structured tool routing beyond current heuristics
- clearer tool-choice logic for multi-step feature work

Best next build:

- improve tool orchestration for small feature tasks and failure diagnosis

### 4. Safety Layer

Status: `done`

What exists:

- workspace path restrictions
- allow/ask/deny permission decisions
- approval gating for risky actions
- bounded command execution

Why this is effectively done for current scope:

- the core bounded-harness safety shape is already present and tested

### 5. Session Layer

Status: `partial`

What exists:

- durable session records
- event logs
- review and resume flows
- compact working-memory snapshots that persist focus, touched files, validation state, and next-step hints

What is missing:

- better long-session continuity
- more explicit distinction between durable transcript and prompt-ready summary

Best next build:

- improve the current working-memory snapshot with stronger long-session compaction and unresolved-question tracking

### 6. Evaluation Layer

Status: `partial`

What exists:

- fixed eval scenarios
- fixed eval coverage for explicit and natural-language bug-intent routing plus natural-language feature requests
- JSON eval artifacts
- artifact listing and history
- label-based resolution
- named baselines
- comparison
- guarded promotion
- saved decision artifacts for compare and auto-promote flows

What is missing:

- broader task coverage
- stronger regression probes for feature work and rename flows
- clearer benchmark grouping by task class

Best next build:

- extend the eval suite to cover the full minimum task set in the capstone brief

## Minimum Task Set Coverage

### Failing-Test Repair

Status: `done`

Evidence:

- current repair loop
- built-in test-oriented flows
- eval coverage around repair behavior

### Small Feature Edit

Status: `partial`

Evidence:

- existing explicit and inferred argparse CLI feature flows
- existing config-option default feature flow
- eval coverage for explicit and natural-language CLI, config-option, and env-var feature requests

What is still missing:

- better planning and deeper validation selection for feature work beyond the current text-and-module matching rules

### Safe Multi-File Rename

Status: `done`

Evidence:

- current exact-match safe rename flow
- demonstrated multi-file rename behavior

### Failure Diagnosis Without Editing

Status: `done`

Evidence:

- the harness can inspect failure output and related files
- the harness now has a first-class diagnose-only flow with explicit no-edit completion behavior

### Resume And Continue A Prior Session

Status: `partial`

Evidence:

- review and resume saved sessions already exist
- resumed sessions now carry a compact working-memory snapshot forward

What is still missing:

- stronger continuity for longer tasks
- more compact session state for resumed runs

## Best Next Implementation Order

To move `coding-agent-v1` toward the flagship capstone, the next work should be:

1. improve the current evidence-based planner rules into a stronger planner
2. improve validation selection beyond the current text-and-module matching rules
3. expand eval scenarios further with broader task variation inside each minimum task class
4. broaden feature-task support beyond the current CLI flag pattern
5. strengthen long-session memory compaction and unresolved-question tracking

The concrete brief for the immediate next milestone is:

- `projects/coding-agent-v1-planner-and-eval-upgrade.md`

## What Not To Do Yet

The highest-leverage next step is not:

- distributed runtime work
- broad subagent fan-out
- cloud orchestration
- heavy sandbox infrastructure

Those may matter later, but they are not the main blockers between the current V1 harness and the flagship capstone.

## Bottom Line

`coding-agent-v1` is already a real harness, not a scaffold.

The shortest path to a strong flagship project is to keep extending it in five areas:

- planner quality
- feature-task support
- compact working memory
- broader eval coverage
- task-aware validation
