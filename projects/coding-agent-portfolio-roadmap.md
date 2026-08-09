# Coding Agent Portfolio Roadmap

## Purpose

This roadmap defines a portfolio of projects around coding agents that builds from fundamentals to a serious end-to-end harness.

The goal is not to produce random experiments.

The goal is to build a sequence of projects where each one teaches a specific part of coding-agent design and together they show real depth on the topic.

## Big-Picture Learning Goal

The main thing this portfolio should teach is:

how to turn an LLM from a model that can talk about code into a bounded engineering system that can do useful work inside a real repository.

That means learning four layers together instead of treating the model as the whole product:

- agent loop and task decomposition
- tools, permissions, and execution control
- memory, context management, and resumability
- evals, regression checks, and operating discipline

If these layers are missing, the result is usually a chatbot with code opinions.

If these layers are present, the result starts to look like a real coding agent.

## Current Repo Position

As of Sunday, August 9, 2026, this repo is no longer at the idea stage.

The active implementation anchor is:

- `projects/coding-agent-v1/`

That project already covers part of the portfolio path:

- repo awareness
- tool use
- permission gating
- session persistence
- working-memory snapshots
- validation loops
- eval artifacts and baseline comparison

Its local test suite is currently passing with:

- `123 passed`

That means the portfolio plan should not assume we are starting from zero.

It should show how to turn the current V1 harness into a sequence of stronger, more visible repo artifacts.

## End-to-End Meaty Goal

The flagship goal for this topic should be:

build a repo-aware coding agent that can take a software task from request to verified patch with logs, bounded tools, approval rules, resumable state, and regression-aware evaluation.

In simple terms, that means the agent should be able to:

- understand the repository it is working in
- inspect and search the right files
- propose and apply targeted changes
- run tests or validation commands
- recover from failures with another attempt
- save what happened so the session can be reviewed or resumed
- compare behavior over time instead of relying on vibes

This is a better capstone than "make an agent that edits files" because it forces the full harness to exist.

## What This Big Goal Teaches

If we build the capstone seriously, it teaches:

- how coding agents are architected in practice
- where the model ends and the harness begins
- why safety and permissions are product features, not optional extras
- why context quality and memory shape agent performance
- why evals and baselines matter more than one-off demos
- how to package research ideas into an engineering system other people can use

## Portfolio Thesis

A strong portfolio in coding agents should demonstrate:

- understanding of agent architecture
- practical tool use
- safety and permission design
- memory and context management
- evaluation discipline
- ability to turn research ideas into working systems

It should also tell a visible story:

1. I can build the core loop.
2. I can make it safe and bounded.
3. I can make it stateful and resumable.
4. I can measure and improve it.
5. I can turn it into a serious engineering tool.

## Recommended Portfolio Sequence

This repo should present the coding-agent topic as five connected projects, not ten disconnected mini-experiments.

The sequence below is the best fit for the current codebase.

## Project 1: Coding Agent V1 Foundation

### Goal

Use `projects/coding-agent-v1/` as the first real implementation artifact: a local repo-aware coding agent that can inspect a repo, choose a task flow, make a bounded change, run validation, and persist session state.

### What It Teaches

- the core agent loop
- repo-aware tool use
- task-flow classification
- validation after edits
- why harness code matters more than a single prompt

### Deliverable

- `projects/coding-agent-v1/`
- demos of inspect, fix, feature, rename, and diagnose flows
- passing local test suite

### What It Shows In A Portfolio

- you can build a non-trivial coding harness end to end
- you understand the difference between model behavior and system behavior

## Project 2: Planner and Validation Upgrade

### Goal

Push `coding-agent-v1` from heuristic V1 behavior into a stronger planning and validation system.

### What It Teaches

- how agents choose among competing task strategies
- why validation selection is part of agent quality
- how repo evidence should shape execution choices

### Deliverable

- stronger planner inside `projects/coding-agent-v1/`
- broader validation heuristics
- better feature-task coverage
- milestone brief in `projects/coding-agent-v1-planner-and-eval-upgrade.md`

### What It Shows In A Portfolio

- you can improve agent quality systematically instead of just adding features
- you know how to make agent behavior more evidence-based and reviewable

## Project 3: Memory and Session Continuity

### Goal

Extend the current session model into something stronger for long-running repo work.

### What It Teaches

- durable transcript vs compact working state
- long-session continuity
- how resumability changes agent product quality

### Deliverable

- stronger working-memory compaction
- unresolved-question tracking
- clearer resume/review artifacts

### What It Shows In A Portfolio

- you understand that useful agents need state, not just one-shot execution

## Project 4: Eval and Regression Discipline

### Goal

Turn the current eval support into a real benchmark layer for coding-agent progress.

### What It Teaches

- measurement discipline
- task-class coverage
- baseline and regression thinking

### Deliverable

- expanded eval scenarios across every minimum task class
- clearer saved artifacts and comparison views
- stable named baselines for repeated checks

### What It Shows In A Portfolio

- you do not rely on demos alone
- you can prove improvements and catch regressions

## Project 5: Flagship Coding Agent Capstone

### Goal

Turn `coding-agent-v1` into the flagship repo artifact described in `projects/coding-agent-flagship-capstone.md`.

### What It Teaches

- full-system integration
- practical tradeoffs
- how all harness components work together

### Deliverable

- a stronger `coding-agent-v1` or successor folder
- written architecture notes
- saved sessions, evals, and comparisons
- demos across the minimum task set

### What It Shows In A Portfolio

- you can take the topic from research review to a serious build
- you can package the result into something reviewable and reusable

## Nice-To-Have Later Projects

These are good follow-on ideas, but they should come after the five-project spine above:

- skills system
- personas and operating modes
- specialized vertical agents
- bounded subagents
- sandbox/runtime hardening

These are valuable because they deepen the harness, but they are not the shortest path to a strong flagship artifact in this repo.

## Best Launch Story For Git

If we want this repo to read clearly to other people, the best story is:

1. `notes/` explains the research and source repos.
2. `projects/coding-agent-v1/` proves the first serious implementation.
3. `projects/coding-agent-v1-gap-analysis.md` explains what is next.
4. `projects/coding-agent-flagship-capstone.md` defines the end state.
5. this roadmap explains the sequence of launches between those points.

## Bottom Line

The portfolio on this topic should show one big lesson:

building a coding agent is really about building the harness around the model.

This repo now has enough implementation weight that the right move is to keep deepening the existing coding-agent line, not restart with disconnected toy projects.
