# Coding Agent V1 Roadmap Alignment

This file maps the harness roadmap in `harness-design/implementation-roadmap.md` against the current implementation in `projects/coding-agent-v1/`.

Reviewed on: August 9, 2026

Primary evidence:

- `projects/coding-agent-v1/README.md`
- `projects/coding-agent-v1/src/coding_agent_v1/agent_loop.py`
- `projects/coding-agent-v1/src/coding_agent_v1/planner.py`
- `projects/coding-agent-v1/src/coding_agent_v1/session_store.py`
- `projects/coding-agent-v1/src/coding_agent_v1/eval_harness.py`

## Simple Status

Big picture:

- the project is past "toy scaffold"
- the single-agent harness loop is real
- safety, persistence, and eval discipline are already materially implemented
- long-running context management is implemented for the first serious local proof
- model-backed planning is still incomplete
- subagents do not exist yet

In simple words:

`coding-agent-v1` already proves that we can build a real local coding-agent harness. It does not yet prove model-guided planning, subagent delegation, or a self-improving harness loop.

## Phase-By-Phase Alignment

## Phase 0: System Contract

Status: `mostly done`

Evidence:

- explicit task types exist: `inspect`, `fix`, `feature`, `rename`, `diagnose`, and resume behavior
- planner emits structured `TaskPlan` data with flow, strategy, initial actions, validation command, and reasons
- eval result and comparison structures exist
- session records and working-memory summaries exist

What is still weak:

- artifact schema is documented for reviewer use, but not yet versioned as a public compatibility contract
- success and failure schemas exist in code and docs, but compatibility policy is still informal

Conclusion:

- good enough for implementation
- not yet hardened as a formal platform contract

## Phase 1: Minimum Working Loop

Status: `done`

Evidence:

- `agent_loop.py` classifies task flow, builds a plan, chooses actions, executes tools, and runs validation
- `workspace.py`, `tools.py`, `validator.py`, and `permissions.py` are wired into the loop
- README documents repo inspection, edit flows, validation, and final reporting

What this shows:

- the core loop is not hypothetical anymore

## Phase 2: Safety And Enforcement

Status: `mostly done`

Evidence:

- explicit permission gating exists
- workspace-bound decisions exist
- risky actions can require approval
- validation is part of the normal success path
- tool execution is bounded and logged through the session model

What is still weak:

- approval UX is still basic
- hooks/rules are implemented more as runtime checks than as a richer enforcement layer
- safety policy looks local and practical, not yet deeply extensible

Conclusion:

- enough for a credible v0/v1 harness
- still room to mature into a stronger policy surface

## Phase 3: Durable Memory And Resumption

Status: `mostly done`

Evidence:

- `session_store.py` persists session records as JSON
- `SessionRecord` includes plan, events, inspected files, changed files, validation summary, final report, and working memory
- README explicitly lists review and resume of saved sessions, compact BPE continuation, handoff artifacts, and repair records

What is still weak:

- current memory is a practical BPE artifact layer, not a learned or model-ranked memory system
- resumability is implemented locally, but not yet stress-tested across very large repositories or multi-day task chains

Conclusion:

- this phase is complete for the local v1 proof, with larger long-horizon scaling left for later

## Phase 4: Eval Harness

Status: `done`

Evidence:

- `eval_harness.py` contains executable scenario structures, summaries, comparisons, promotion decisions, artifact index, history, audit, and prune models
- README describes built-in, smoke, core, and stress eval packs
- README documents saved artifacts, baseline promotion, regression comparison, history, and pack-aware filtering

What this shows:

- the project already crossed the line from "demo agent" to "measured harness"

## Phase 5: Long-Running Workflow Support

Status: `mostly done for local v1`

Evidence:

- compact BPE continuation artifacts exist under `compactions/`
- handoff artifacts exist under `handoffs/`
- handoff resume is available through CLI
- compaction trigger metadata is persisted and surfaced in eval traces
- procedural repair records capture approval, permission, and validation boundaries
- flagship evidence proves compact resume, handoff resume, repair memory, and clean resume eval behavior

What is missing:

- model-ranked memory retrieval
- larger retention policy around accumulated repair-status audits
- broader stress coverage for very long session chains

Conclusion:

- the current system supports a credible local long-running workflow
- production-scale long-horizon memory remains future work

## Phase 6: Delegation And Parallelism

Status: `missing`

Evidence:

- no subagent orchestration modules are present in `coding-agent-v1`
- no parent-child artifact merge model is documented

Conclusion:

- this should stay out of scope until the long-running single-agent loop is stronger

## Current Overall Rating Against The Roadmap

If the roadmap target is `coding-agent-harness-v0`, current status is roughly:

- core loop: `done`
- safety: `mostly done`
- persistence/resume: `mostly done`
- evals: `done`
- long-running execution: `partial`
- subagents: `not started`

That means the current implementation is already a legitimate `v0.8` to `v1.0` style harness, not a blank start.

## What The Current System Already Proves

The current implementation already proves:

- task routing can be structured and testable
- validation can be selected intentionally instead of always running the whole suite
- session state can be persisted and reviewed
- eval runs can be saved, compared, and promoted
- the harness can be improved through explicit benchmark discipline

This is already the practical core of harness engineering.

## What It Does Not Yet Prove

It does not yet prove:

- a real LLM-guided planner
- production-scale long-horizon memory retrieval
- bounded subagent delegation
- harness self-improvement based on mined failure patterns

Those are the next serious layers.

## Recommended Next Build Order

The best next sequence is:

1. implement `model_guided` planning behind the existing deterministic task-plan contract
2. add planner-quality eval packs before enabling non-deterministic planning by default
3. expand stress evals around long resume chains and validation ambiguity
4. harden artifact retention for long-running local use
5. only then consider subagent design

This is better than adding broad new features, because it deepens the actual harness thesis.

## Issue-Ready Next Steps

These are the best next tickets to open now.

## Issue 1: Expand Planner-Quality Gate

Goal:

- add harder planner-quality evals for the `model_guided` subprocess planner while preserving the deterministic planner as the default baseline

Why:

- the real Codex-backed planner path now runs and passes the parity gate; it still must prove it improves quality rather than just adding variability

Done when:

- planner interface supports a model-backed backend
- current scored planner is preserved as baseline backend
- task-plan outputs remain stable
- tests cover deterministic fallback and unsupported-strategy boundaries
- evals show the model-backed planner has no regression against the deterministic baseline

## Issue 2: Add Planner Quality Eval Pack

Goal:

- create eval pressure specifically for planner strategy quality

Why:

- model-backed planning should be gated by behavior evidence, validation choice, tool sequence, and escalation behavior

Done when:

- scenarios compare deterministic and model-guided planner choices
- planner mistakes are visible in eval artifacts
- baseline comparison can show planner regressions by task class and behavior ID

## Issue 3: Harden Long-Run Artifact Retention

Goal:

- keep long-running artifact directories usable as sessions, compactions, handoffs, repairs, traces, and audits accumulate

Why:

- the harness now creates useful artifacts; retention must keep reviewability without unbounded noise

Done when:

- repair-status audit retention exists if audit volume becomes noisy
- compaction retention remains dry-run by default and protects important continuations
- reviewer docs explain what is safe to prune

## Issue 4: Expand Resume Eval Coverage

Goal:

- make resume quality measurable instead of assumed

Why:

- resume exists, but long-running reliability is still under-tested

Done when:

- eval suite includes multiple interrupted-run scenarios
- scenarios cover resumed diagnosis, resumed repair, and resumed feature flow
- regressions in resumed outcome quality are visible in comparisons

## Issue 5: Expand Validation-Selection Evals

Goal:

- harden targeted validation selection with broader benchmarks

Why:

- targeted validation is one of the strongest current features and one of the easiest places to regress

Done when:

- eval scenarios cover explicit test references, implicit module-aware matching, nested test paths, and ambiguity fallback
- validation reasons remain visible in artifacts

## Issue 6: Formalize Artifact Contract

Goal:

- document the saved session, eval, and decision artifact shapes as a stable repo contract

Why:

- the code already saves useful artifacts, but reviewers should not have to infer the structure from implementation

Done when:

- artifact types and fields are documented
- expected producer/consumer flow is written down
- backward-compatibility expectations are stated

## Issue 7: Add Planner Failure Review Loop

Goal:

- record planner misses explicitly and make them reviewable

Why:

- harness engineering depends on turning repeated misses into better rules or better planner behavior

Done when:

- planner mistakes can be tagged in eval artifacts
- a summary view shows recurring planner failures
- at least one planner-focused regression report exists

## Issue 8: Add Policy Hooks Beyond Approval Decisions

Goal:

- move from "allow/ask/deny" only toward richer enforcement hooks

Why:

- current policy works, but the research docs emphasize hook-based enforcement as a load-bearing harness layer

Done when:

- there is at least one pre-action hook and one post-edit hook
- hook failures are surfaced in artifacts
- regression tests cover hook behavior

## Bottom Line

`projects/coding-agent-v1/` is already real implementation, not just notes.

The clearest next move is not "start over" and not "add subagents".

It is:

- improve planner quality
- strengthen long-running continuation
- expand eval pressure on resume and validation
- formalize the artifact contract

That is the shortest path from current `v1` to a stronger harness that actually reflects the research in `harness-design/`.
