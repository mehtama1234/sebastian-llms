# Flagship Demo Evidence: 2026-08-09

Artifact root:

```text
projects/coding-agent-v1/.coding-agent-v1/demo-sessions-20260809-173926/
```

This bundle was generated from the current worktree during the flagship proof run. The eval artifacts were created on `2026-08-10T00:41Z`; the directory name reflects the local shell timestamp.

## 1. Behavior-Aware Planning

Session:

```text
10ff5add1c974d2b93993818a75b7d63
```

Review command:

```bash
PYTHONPATH=src python3 -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions-20260809-173926 \
  --review-session 10ff5add1c974d2b93993818a75b7d63
```

Evidence:

- request: `improve validation selection for rename tasks`
- task plan includes `planner_strategy=deterministic_heuristic`
- task plan includes `behaviors=task_planning,validation_selection`
- task plan includes implementation surfaces for `agent_loop.py`, `models.py`, and `planner.py`
- BPE belief includes the affected behavior state

## 2. Compact BPE Continuation

Compact artifact:

```text
.coding-agent-v1/demo-sessions-20260809-173926/compactions/10ff5add1c974d2b93993818a75b7d63.compact.json
```

Review command:

```bash
PYTHONPATH=src python3 -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions-20260809-173926 \
  --review-compact-context 10ff5add1c974d2b93993818a75b7d63
```

Resume session:

```text
b9aae2894ae24cd1bd157b46602db006
```

Evidence:

- compact artifacts preserve affected behavior IDs, implementation surfaces, belief, progress, next step, and trigger metadata
- resume flow uses compact continuation state instead of replaying raw logs
- compact prune dry-run reported `prunable: 1` while protecting important size-triggered compactions by default

## 3. Handoff On Blocked Execution

Blocked session:

```text
f19bfaa158a7456db6fb9134177c201d
```

Handoff artifact:

```text
.coding-agent-v1/demo-sessions-20260809-173926/handoffs/f19bfaa158a7456db6fb9134177c201d.handoff.json
```

Handoff resume session:

```text
5eb4b8e99fd54cf28ffbf12849c43f43
```

Evidence:

- blocked run stopped at an approval boundary
- handoff records blocker, next step, affected behaviors, and BPE continuation state
- resumed run carries forward the prior handoff context

## 4. Procedural Repair Memory

Repair record:

```text
.coding-agent-v1/demo-sessions-20260809-173926/repair-records/f19bfaa158a7456db6fb9134177c201d-approval-required.json
```

Review command:

```bash
PYTHONPATH=src python3 -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions-20260809-173926 \
  --review-repair-record f19bfaa158a7456db6fb9134177c201d-approval-required
```

Evidence:

- `status: candidate`
- `task_class: fix`
- `failure_pattern: approval_required`
- repair records can be reviewed and lifecycle-updated through CLI audit commands

## 5. Core Eval Proof

Eval artifact:

```text
.coding-agent-v1/demo-sessions-20260809-173926/eval-artifacts/eval-summary-e6c7b9e33c4340bf82cb3f3827ab3de2.json
```

Run result:

- `run_label: demo-core`
- `scenario_pack_id: coding-agent-v1-core`
- `passed: 20`
- `failed: 0`
- `trace_count: 20`
- `tool_sequence_match: 20/20`
- `escalation_match: 20/20`

Important scenario evidence:

- `resume-002` passed with `tool_sequence_ok=ok`
- `resume-002` used compact context
- `resume-002` recorded `planner_strategy=deterministic_heuristic`
- `resume-002` recorded `compaction_trigger=size_triggered:resume_checkpoint`
- rename scenarios include `behavior_ids=task_planning,validation_selection`
- diagnose failure-boundary scenarios include repair record IDs
- all scenarios include BPE memory

## 6. Trace-Oriented Smoke Eval Proof

Eval artifact:

```text
.coding-agent-v1/demo-sessions-20260809-173926/eval-artifacts/eval-summary-2e0f901362d24b20b066944ff25037ac.json
```

Run result:

- `run_label: demo-agent-evals-smoke`
- `scenario_pack_id: coding-agent-v1-agent-evals-smoke`
- `passed: 5`
- `failed: 0`
- `trace_count: 5`
- `tool_sequence_match: 5/5`
- `escalation_match: 5/5`

## 7. Baseline Comparison

Baseline config:

```text
.coding-agent-v1/demo-sessions-20260809-173926/eval-artifacts/named-baselines.json
```

Candidate eval artifact:

```text
.coding-agent-v1/demo-sessions-20260809-173926/eval-artifacts/eval-summary-72236ed9677f4cb781ed7742ece1127a.json
```

Comparison result:

- `regressions: 0`
- `expectation_regressions: 0`
- `unchanged: 20`
- `baseline_scenario_pack_id: coding-agent-v1-core`
- `candidate_scenario_pack_id: coding-agent-v1-core`
- baseline tool-sequence match: `20/20`
- candidate tool-sequence match: `20/20`
- baseline escalation match: `20/20`
- candidate escalation match: `20/20`

## Evidence Bundle Summary

The artifact bundle proves:

1. behavior localization for `validation_selection`
2. source-backed implementation surfaces in the plan
3. deterministic planner-strategy recording
4. persisted BPE memory
5. compact continuation artifacts with trigger metadata
6. compact-context use during resume
7. handoff on approval-boundary failure
8. handoff resume
9. candidate procedural repair memory
10. core eval proof across 20 scenarios
11. trace-oriented smoke eval proof across 5 scenarios
12. baseline comparison with zero regressions
13. real Codex-backed `model_guided` planner execution behind the stable `TaskPlan` contract
14. planner-quality gate parity against the deterministic baseline

## 8. Codex-Backed Planner Quality Gate

Artifact root:

`projects/coding-agent-v1/.coding-agent-v1/planner-quality-codex-gate-20260809-182449/`

Evidence:

- deterministic baseline: `eval-summary-04b3e978ba694a169a8400b5d20a4759.json`
- Codex-backed model-guided candidate: `eval-summary-662e5d433b5d4f1ebb0337e0f801bedb.json`
- comparison artifact: `eval-comparison-e05cd79bb89c4981adfa7dc9ad58f957.json`
- baseline passed: `10/10`
- candidate passed: `10/10`
- regressions: `0`
- expectation regressions: `0`
- tool sequence: baseline `10/10`, candidate `10/10`
- escalation: baseline `10/10`, candidate `10/10`

Interpretation:

- `model_guided` is now a real opt-in Codex-backed planner path.
- `deterministic_heuristic` remains the default because the current gate proves parity and safety, not superiority.
- The next step is harder planner evals where the model planner must improve planning choices rather than merely match the baseline.
