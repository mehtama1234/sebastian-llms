# V1 Architecture

Derived from:

- `notes/coding-agents-summary.md`
- `notes/building-a-coding-agent-from-scratch-course-summary.md`
- `projects/v1-build-plan.md`

## Purpose

This document defines the target architecture for the first serious coding-agent build in this repo.

The design goal is not maximum complexity.

The design goal is to reach a complete local loop that can take a real repo task from request to verified result.

## System Shape

The V1 system should have seven core parts:

1. session entrypoint
2. workspace context
3. agent loop
4. tools
5. permission gate
6. session memory
7. validation and reporting

## High-Level Flow

1. User submits a coding request.
2. System gathers workspace context.
3. Agent loop decides what to inspect first.
4. Tools return bounded results.
5. Permission gate approves, denies, or pauses risky actions.
6. Agent applies edits.
7. Validation runs.
8. Session state is saved.
9. Final result is reported.

## Core Components

### 1. Session Entrypoint

Responsibilities:

- start a session
- accept a user request
- initialize workspace context
- load or create session state

Possible outputs:

- session id
- initial request event
- workspace snapshot

### 2. Workspace Context

Responsibilities:

- detect repo root
- collect branch and git status
- find key instructions and project files
- summarize workspace layout

Why it matters:

- most coding tasks are underspecified without repo context

### 3. Agent Loop

Responsibilities:

- interpret the request
- choose the next tool action
- incorporate tool results
- decide when to edit, verify, or stop

Minimal loop shape:

- observe
- inspect
- choose
- act
- verify
- report

### 4. Tool Layer

Required V1 tools:

- `read_file`
- `search_code`
- `edit_file`
- `run_command`
- `request_approval`

Tool rules:

- inputs should be structured
- outputs should be bounded
- errors should be explicit

### 5. Permission Gate

Responsibilities:

- classify requested actions
- allow safe reads automatically
- require approval for risky edits or commands
- deny actions outside workspace rules

Minimal policy model:

- allow
- ask
- deny

### 6. Session Memory

Responsibilities:

- store a full event transcript
- maintain a smaller working summary
- preserve changed files, commands, and outcomes

Why it matters:

- coding tasks are multi-step and need continuity

### 7. Validation and Reporting

Responsibilities:

- run targeted tests or checks after changes
- record whether verification passed
- produce a concise engineering-style summary

Why it matters:

- the agent is not done when it writes code
- it is done when it can justify the result

## Data Boundaries

### Stable Context

This changes infrequently:

- repo summary
- tool descriptions
- permission policy

### Dynamic Context

This changes every turn:

- latest user request
- tool outputs
- working memory
- recent transcript

This separation is important because it reduces prompt noise and makes caching easier later.

## V1 Non-Goals

These should not block the first serious build:

- cloud runtimes
- distributed execution
- subagent fan-out
- full eval harness
- full LSP integration
- advanced skill system

## Architecture Principle

Keep the agent loop thin and keep the harness explicit.

That means:

- tool behavior belongs in the tool layer
- safety belongs in the permission layer
- continuity belongs in memory/session storage
- correctness belongs in validation

## Example V1 Request Lifecycle

Example request:

`Fix the failing test in this repo.`

Expected lifecycle:

1. gather repo summary
2. inspect test files and failure output
3. identify likely source file
4. request approval if an edit is needed
5. apply a minimal change
6. rerun the failing test
7. record outcome
8. report what changed and whether the test passed

## Bottom Line

V1 should teach us how to build a complete coding-agent harness with the smallest set of parts that still produce a trustworthy result.
