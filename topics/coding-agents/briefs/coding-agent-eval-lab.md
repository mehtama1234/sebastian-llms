# Coding Agent Eval Lab

## Purpose

Turn `projects/coding-agent-v1/` from a harness with a built-in smoke suite into a benchmarked coding-agent system with broader external evaluation coverage.

## Why This Project Exists

The current package already has:

- a fixed in-code eval suite
- persisted eval artifacts
- artifact comparison
- named baselines
- guarded promotion
- history summaries

What it still lacks is a durable external evaluation layer with:

- broader scenario coverage
- balanced task-class representation
- explicit failure-mode taxonomy
- scenario-pack growth that does not require expanding a hard-coded Python list first

## Target Deliverable

An eval lab for `coding-agent-v1` with:

- external scenario packs under `evals/coding-agent-v1/scenarios/`
- rubrics for pass/fail and failure classification
- package code that can load and summarize scenario packs
- later, package code that can execute those scenario packs directly

## First Milestone

The first milestone is intentionally narrow:

1. define a stable external scenario-pack format
2. create a balanced core pack
3. document rubric language
4. add package code that loads and summarizes the external pack

That milestone is enough to make the eval expansion real without rewriting the existing harness.

## Core Task Classes

- `fix`
- `feature`
- `rename`
- `diagnose`
- `resume`

## Core Failure Types

- `wrong_file_touched`
- `no_op`
- `partial_fix`
- `bad_validation_scope`
- `unsafe_action`
- `regression_introduced`
- `resume_memory_loss`
- `diagnose_edited_repo`

## Near-Term Build Order

1. loader and summary support for external scenario packs
2. core external pack with at least 20 scenarios
3. execution bridge from external pack into the current eval harness
4. richer artifact summaries grouped by task class and failure mode
5. baseline comparisons that report regressions by task class

## Success Criteria

This project becomes useful when a future run can answer:

- which task classes are improving
- which task classes are regressing
- which failure modes dominate current failures
- whether planner, validation, or memory changes actually improve the system
