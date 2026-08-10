# V1 Demo Scenarios

Derived from: `projects/v1-build-plan.md`

## Purpose

These scenarios define what the first coding-agent build should be able to demonstrate in a credible way.

The goal is not flashy output.

The goal is to prove that the harness can do useful engineering work.

## Demo 1: Fix a Failing Test

### Scenario

A small repository contains one failing unit test.

### What the Agent Should Do

1. inspect the repo
2. run or inspect the failing test
3. locate the likely source file
4. edit the code
5. rerun the test
6. report the fix

### What This Demonstrates

- repo awareness
- tool use
- targeted editing
- validation

### Why It Matters

This is the strongest first demo because it proves the full loop from diagnosis to verified result.

## Demo 2: Add a Small Feature

### Scenario

A repo needs a small change such as a new CLI flag or config option.

### What the Agent Should Do

1. inspect the relevant code path
2. identify where the feature belongs
3. make the required edit across 1-3 files
4. run an appropriate validation command
5. summarize the change

### What This Demonstrates

- feature implementation
- multi-file reasoning
- bounded task completion

## Demo 3: Safe Rename

### Scenario

A symbol or configuration name needs to be renamed across multiple files without breaking behavior.

### What the Agent Should Do

1. search for all references
2. identify the safe rename set
3. apply minimal edits
4. run validation if available
5. summarize affected files

### What This Demonstrates

- code search discipline
- precise editing
- change tracking

## Demo 4: Explain a Failure Before Editing

### Scenario

A failing command or broken test exists, but the first task is diagnosis rather than immediate modification.

### What the Agent Should Do

1. gather failure evidence
2. inspect relevant files
3. explain the likely cause
4. recommend or request the next step

### What This Demonstrates

- analysis before action
- disciplined tool use
- ability to stop before unsafe edits

## Demo 5: Permission Boundary

### Scenario

The agent attempts a risky command or a write outside the approved workspace.

### What the Agent Should Do

1. classify the action as risky or disallowed
2. ask for approval or deny it
3. explain why the action was blocked

### What This Demonstrates

- harness safety
- policy enforcement
- predictable behavior

## What A Good Demo Set Teaches

Together these demos teach:

- the agent can inspect and reason about real code
- the agent is not blindly editing
- the agent can validate its own work
- the harness controls risky behavior
- the session produces reviewable outcomes

## Recommended Order

1. Fix a failing test
2. Explain a failure before editing
3. Add a small feature
4. Safe rename
5. Permission boundary

## Bottom Line

If these demos work, we will have evidence that the coding agent is functioning as an engineering system rather than as a chat wrapper around an LLM.
