# Agent Evals Datasets

This folder should hold gold data for agent evaluation.

## Current files

- `trace-schema-v1.json`
  - the first shared JSON schema for multi-step agent traces
- `sample-success-trace.json`
  - a coding-agent-style successful repair trace
- `sample-unsafe-write-trace.json`
  - a trace where the write action completed but should be graded unsafe

## Dataset classes

- `tool-calls`
  - single-step examples with expected tool and arguments
- `traces`
  - multi-step runs with labeled first-failure states
- `outcomes`
  - final world-state expectations for end-to-end tasks
- `runtime-checks`
  - examples where a cheap check should allow, block, retry, or escalate

## Working rule

Use synthetic data first when we need control over exact failure placement.

Then add real or replayed traces to measure variation from real workloads.

The point is to have both:

- clean gold tasks for stable regression testing
- messy real traces for realism
