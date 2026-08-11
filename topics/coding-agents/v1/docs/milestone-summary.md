# Coding Agent V1 Milestone Summary

Date: August 9, 2026

## Milestone Claim

`coding-agent-v1` now has the first complete behavior-aware harness substrate:

- behavior-indexed planning
- BPE working memory
- compact continuation artifacts
- handoff and resume
- procedural repair memory
- external eval packs
- trace artifacts
- baseline comparison
- reviewer documentation and a concrete evidence bundle

This is not an LLM-backed autonomous software engineer. It is a local, deterministic harness foundation that proves the core state, artifact, safety, and evaluation loops.

## Requirement Audit

### Behavior Index

Status: implemented

Evidence:

- `src/coding_agent_v1/behavior_index.py`
- `tests/test_behavior_index.py`
- flagship evidence session `10ff5add1c974d2b93993818a75b7d63`

Reviewer check:

- validation-selection requests produce `validation_selection`
- implementation surfaces resolve correctly from both package root and monorepo root

### Behavior-Guided Planning

Status: implemented

Evidence:

- `TaskPlan.affected_behavior_ids`
- `TaskPlan.implementation_surfaces`
- `TaskPlan.planner_strategy`
- `TaskPlan.planner_strategy_reason`
- `build_task_plan(...)`
- session review output in `docs/flagship-demo-evidence-20260809.md`

Reviewer check:

- task plans include planner strategy, behavior IDs, implementation surfaces, validation command, and rationale

### BPE Working Memory

Status: implemented

Evidence:

- `WorkingMemory.belief`
- `WorkingMemory.progress`
- `WorkingMemory.experience`
- session JSON artifacts
- review summaries

Reviewer check:

- meaningful runs include non-empty belief and progress
- resume runs include prior-context evidence in experience

### Handoff And Resume

Status: implemented

Evidence:

- `HandoffArtifact`
- `SessionStore.save_handoff(...)`
- `--review-handoff`
- `--resume-handoff`
- flagship blocked session `f19bfaa158a7456db6fb9134177c201d`
- flagship handoff-resume session `5eb4b8e99fd54cf28ffbf12849c43f43`

Reviewer check:

- approval-blocked runs write handoffs
- handoff resume carries BPE continuation state

### Context Compaction

Status: implemented for explicit saved compact continuation artifacts with trigger metadata

Evidence:

- `CompactContextArtifact`
- `SessionStore.save_compact_context(...)`
- `--review-compact-context`
- `--list-compact-contexts`
- `--prune-compact-contexts`
- `CompactContextArtifact.compaction_trigger`
- `CompactContextArtifact.source_event_count`
- `CompactContextArtifact.source_context_chars`
- eval result field `used_compact_context`
- eval result field `compaction_trigger`
- trace field `harness_state.used_compact_context`
- trace field `harness_state.compaction_trigger`
- trace field `harness_state.planner_strategy`
- flagship compact artifact for session `10ff5add1c974d2b93993818a75b7d63`

Reviewer check:

- compact artifacts are written beside session records
- normal session compactions are marked as `checkpoint`
- long or blocked sessions are marked with `size_triggered:*` reasons
- compact context prune plans are dry-run by default and protect size-triggered compactions unless explicitly included
- `--resume-session` prefers compact context when available
- resume evals report `compact_context=true`

### Procedural Repair Memory

Status: implemented as reviewable candidate repair records with explicit lifecycle updates

Evidence:

- `ProceduralRepairRecord`
- `SessionStore.save_procedural_repair_record(...)`
- `--list-repair-records`
- `--review-repair-record`
- `--set-repair-record-status`
- `--list-repair-status-audits`
- `--review-repair-status-audit`
- flagship repair record `f19bfaa158a7456db6fb9134177c201d-approval-required`

Reviewer check:

- approval, permission, and validation failures write candidate repair records
- later matching task flows recall accepted repairs first, then candidate repairs into experience
- reviewers can set repair status to `candidate`, `accepted`, `rejected`, or `retired`
- each explicit repair status update writes an audit artifact with previous status, new status, actor, reason, and timestamp

### Eval Pressure

Status: implemented

Evidence:

- `evals/coding-agent-v1/scenarios/smoke-v1.json`
- `evals/coding-agent-v1/scenarios/core-v1.json`
- `evals/coding-agent-v1/scenarios/stress-v1.json`
- `evals/agent-evals/scenarios/coding-agent-v1-smoke-v1.json`
- `EvalResult.behavior_ids`
- `EvalResult.repair_record_ids`
- `EvalResult.has_bpe_memory`
- `EvalResult.used_compact_context`
- trace aggregate summaries
- baseline comparison artifacts

Reviewer check:

- core eval pack passed `20/20`
- agent-evals smoke pack passed `5/5`
- baseline comparison reported `regressions: 0`

Expectation-check status:

- current flagship demo evidence reports `resume-002` with `tool_sequence_ok=ok`
- current flagship baseline comparison reports `tool_sequence: baseline=20/20 candidate=20/20`

### Reviewer Package

Status: implemented

Evidence:

- `docs/artifact-contract.md`
- `docs/flagship-demo-runbook.md`
- `docs/flagship-demo-evidence-20260809.md`
- `docs/model-guided-planner-gate.md`
- this milestone summary

Reviewer check:

- an engineer can inspect artifacts, rerun the demo, and compare evals without needing verbal context

## Verification

Latest focused harness verification:

```text
246 passed in 350.62s
```

Additional focused check after this summary/docs cleanup:

```text
64 passed in 4.65s
```

## Not In Scope For This Milestone

- autonomous self-editing without review
- real model-backed planning
- reinforcement learning
- multi-agent orchestration
- production sandboxing
- large-repo scaling

## Next Sensible Work

1. Add harder model-backed planner eval packs where `model_guided` must outperform, not only match, the deterministic baseline.
2. Keep `deterministic_heuristic` as the default until those harder packs show stable model-guided improvement.
3. Add retention controls for old repair-status audit artifacts if audit volume becomes noisy.

Implementation gate:

- `docs/model-guided-planner-gate.md`
- `scripts/run_planner_quality_gate.sh`
- `scripts/run_planner_superiority_gate.sh`
- current script-run planner-quality gate check reports deterministic baseline `10/10`, Codex-backed model-guided candidate `10/10`, `regressions: 0`, and `expectation_regressions: 0`
- latest gate artifact root: `.coding-agent-v1/planner-quality-codex-gate-20260809-182449/`
- current planner-superiority gate check reports deterministic baseline `6/10`, Codex-backed model-guided candidate `6/10`, `regressions: 0`, `expectation_regressions: 0`, and `improvements: 0`
- latest superiority artifact root: `.coding-agent-v1/planner-superiority-codex-gate-20260809-185700/`
- superiority result: gate failed, so `model_guided` remains opt-in and should not become default
