# Agent Evals

Evaluation scaffolding for tool-using and multi-step agents.

This folder is the benchmark layer for the `docs/agent-evals/` and `projects/agent-evals/` track.

## Primary questions

1. Did the agent choose the right tool or action?
2. Did it generate correct and safe arguments?
3. Did the tool succeed?
4. Did the model use the tool output correctly?
5. Did the overall run achieve the right outcome safely?
6. If not, where did the first real failure happen?

## Eval categories

- `stage-level`
  - tool selection
  - argument quality
  - execution success
  - output handling
- `trace-level`
  - first-failure attribution
  - loop detection
  - premature stop
  - unsafe persistence across steps
- `outcome-level`
  - task success
  - safety
  - escalation correctness
- `runtime`
  - grounding checks
  - high-risk action gates
  - agreement checks

## Current files

- `benchmark-plan.md`
  - what scenario families and measurements to build first
- `rubrics.md`
  - how to score success, failure, and safety
- `datasets/README.md`
  - what kinds of gold data belong here
- `scenarios/README.md`
  - the scenario-pack structure we should build next
- `datasets/trace-schema-v1.json`
  - first shared trace schema for multi-step agent runs
- `scenarios/schema-v1.json`
  - first schema for richer agent-eval scenario packs

## First integration target

The first real consumer of this folder should be:

- `projects/coding-agent-v1/`

That is the fastest path from theory to something runnable in this repo.
