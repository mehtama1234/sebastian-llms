# Coding Agent V1 Artifact Contract

This document defines the artifacts a reviewer should inspect to understand a `coding-agent-v1` run without reading raw terminal output.

## Artifact Root

By default, artifacts are written under:

```text
.coding-agent-v1/sessions/
```

The root can be changed with:

```bash
python -m coding_agent_v1.cli --session-dir <path> ...
```

## Session Record

Path:

```text
<session-dir>/<session-id>.json
```

Purpose:

- durable record of one agent run
- source of truth for request, task plan, tool events, working memory, validation, and final report

Required reviewer questions it answers:

- What did the user ask?
- What task flow was selected?
- What behavior IDs and implementation surfaces were selected?
- What files were inspected or changed?
- What validation command was selected?
- What was the final status and report?

Important fields:

- `session_id`
- `request`
- `workspace_root`
- `task_flow`
- `task_plan`
- `task_plan.planner_strategy`
- `task_plan.planner_strategy_reason`
- `task_plan.affected_behavior_ids`
- `task_plan.implementation_surfaces`
- `task_plan.validation_command`
- `task_plan.reasons`
- `events`
- `inspected_files`
- `changed_files`
- `working_memory`
- `working_summary`
- `validation_summary`
- `final_report`

Review command:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --review-session <session-id>
```

Planner strategy contract:

- `deterministic_heuristic` is the default strategy today.
- `model_guided` is a recognized opt-in strategy name that executes `CODING_AGENT_V1_MODEL_PLANNER_COMMAND` as a bounded subprocess planner.
- enabling real `model_guided` planning requires a model planner implementation that still returns the same `TaskPlan` fields and passes evals before it can become the default CLI strategy.

## BPE Working Memory

Stored inside:

```text
<session-dir>/<session-id>.json
```

Purpose:

- compact runtime state for long-running agent work
- separates current facts from progress and reusable experience

Fields:

- `working_memory.belief`
- `working_memory.progress`
- `working_memory.experience`

Belief should include:

- selected task flow
- workspace identity
- affected behavior IDs when known
- inspected evidence
- validation state

Progress should include:

- planned initial actions
- changed files
- validation state
- next step

Experience should include:

- resumed session or handoff references
- recalled repair records
- important planner or validation lessons

Completion check:

- meaningful runs should have non-empty `belief` and `progress`
- resume runs should include prior-session, handoff, or compact-context evidence in `experience`

## Compact Context Artifact

Path:

```text
<session-dir>/compactions/<session-id>.compact.json
```

Purpose:

- BPE-shaped continuation artifact
- avoids replaying full raw event history during resume

Required reviewer questions it answers:

- What state is preserved for continuation?
- What behavior IDs are still active?
- What files matter?
- What validation or blocker state must survive?
- What should the next run do?

Important fields:

- `session_id`
- `request`
- `status`
- `task_flow`
- `compaction_trigger`
- `source_event_count`
- `source_context_chars`
- `affected_behavior_ids`
- `implementation_surfaces`
- `belief`
- `progress`
- `experience`
- `inspected_files`
- `changed_files`
- `validation_summary`
- `blocker`
- `next_step`
- `summary`

Review command:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --review-compact-context <session-id>
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-compact-contexts
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-compact-contexts --prune-compact-keep-newest 20
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-compact-contexts --prune-compact-contexts-apply
```

Resume behavior:

- `--resume-session <session-id>` loads the full session record
- when a compact context exists for that session, the new run prefers the compact BPE continuation state
- normal session compactions are marked as `checkpoint`
- long or blocked session compactions are marked with `size_triggered:*` reasons
- eval summaries expose this as `compact_context=true`
- trace artifacts expose this as `harness_state.used_compact_context`
- compaction pruning is dry-run by default
- pruning keeps the newest artifacts and protects `size_triggered:*` compactions unless `--prune-compact-include-size-triggered` is provided

## Handoff Artifact

Path:

```text
<session-dir>/handoffs/<session-id>.handoff.json
```

Purpose:

- explicit continuation package for blocked or incomplete runs
- intended for fresh-session recovery after approval, permission, or validation failure

Created when:

- a tool request is denied
- a command requires approval and approval was not provided
- validation runs and remains failed

Important fields:

- `session_id`
- `request`
- `status`
- `reason`
- `task_flow`
- `affected_behavior_ids`
- `belief`
- `progress`
- `experience`
- `inspected_files`
- `changed_files`
- `validation_summary`
- `blocker`
- `next_step`

Review command:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --review-handoff <session-id>
```

Resume command:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --resume-handoff <session-id> "continue the task"
```

Completion check:

- the handoff must preserve enough BPE state for a later run to continue without replaying raw logs

## Procedural Repair Record

Path:

```text
<session-dir>/repair-records/<repair-id>.json
```

Purpose:

- reviewable failure-memory artifact
- captures a reusable recovery pattern from approval, permission, or validation failures

Important fields:

- `repair_id`
- `source_session_id`
- `task_class`
- `trigger_condition`
- `failure_pattern`
- `recommended_recovery`
- `source_evidence`
- `validation_evidence`
- `affected_behavior_ids`
- `support_count`
- `status`

Allowed statuses:

- `candidate`
- `accepted`
- `rejected`
- `retired`

Review commands:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-repair-records
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --review-repair-record <repair-id>
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --set-repair-record-status <repair-id> accepted --repair-status-reason "validated repeated fix"
```

Completion check:

- failed validation should create a candidate repair record
- later matching task flows should recall accepted or candidate repair records into `working_memory.experience`
- repair records should be explicitly promotable to `accepted`, `rejected`, or `retired` without editing JSON by hand
- repair status changes should write audit artifacts

## Procedural Repair Status Audit

Path:

```text
<session-dir>/repair-status-audits/<audit-id>.json
```

Purpose:

- immutable review record for procedural repair status changes
- explains who or what changed a repair status and why

Important fields:

- `audit_id`
- `repair_id`
- `previous_status`
- `new_status`
- `actor`
- `reason`
- `created_at`

Review commands:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-repair-status-audits
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-repair-status-audits <repair-id>
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --review-repair-status-audit <audit-id>
```

Completion check:

- every explicit repair status update should create one audit artifact
- audit review should show previous status, new status, actor, timestamp, and reason when provided

## Eval Summary Artifact

Path:

```text
<session-dir>/eval-artifacts/eval-summary-<uuid>.json
```

Purpose:

- repeatable measurement of harness behavior
- supports pass/fail, task-class breakdowns, failure-mode breakdowns, BPE/compact context checks, behavior IDs, repair IDs, and trace links

Important fields:

- `total`
- `passed`
- `failed`
- `run_label`
- `scenario_pack_id`
- `results`
- `results[].task_class`
- `results[].planner_strategy`
- `results[].failure_modes`
- `results[].behavior_ids`
- `results[].repair_record_ids`
- `results[].has_bpe_memory`
- `results[].used_compact_context`
- `results[].compaction_trigger`
- `results[].actual_tool_sequence`
- `results[].tool_sequence_ok`
- `results[].escalation_ok`
- `trace_summary`
- `trace_first_failure_summary`
- `trace_primary_failure_summary`
- `trace_transition_failure_summary`

Run commands:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-eval-pack ../../evals/coding-agent-v1/scenarios/smoke-v1.json
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-eval-pack ../../evals/coding-agent-v1/scenarios/core-v1.json
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-eval-pack ../../evals/coding-agent-v1/scenarios/stress-v1.json
```

Completion check:

- scenario packs may specify `planner_strategy`; omitted values default to `deterministic_heuristic`
- unconfigured, failing, or invalid planner backends should fail through the planner gate before any tool action rather than silently falling back
- resume scenarios should report `compact_context=true`
- eval results should report compact artifact trigger metadata when available
- meaningful runs should report `bpe_memory=true`
- failures should expose task class, behavior IDs, and failure mode

## Eval Trace Artifact

Path:

```text
<session-dir>/eval-artifacts/trace-artifacts/trace-<scenario-id>-<session-id>.json
```

Purpose:

- step-level trace for agent-eval review
- validates against `evals/agent-evals/datasets/trace-schema-v1.json`

Important fields:

- `agent_id`
- `scenario_id`
- `request`
- `task_class`
- `tools_available`
- `steps`
- `outcome`
- `harness_state`
- `harness_state.planner_strategy`
- `harness_state.behavior_ids`
- `harness_state.belief`
- `harness_state.progress`
- `harness_state.experience`
- `harness_state.has_bpe_memory`
- `harness_state.used_compact_context`
- `harness_state.compaction_trigger`
- `expected`
- `expectation_checks`
- `labels`

Completion check:

- trace artifacts should validate against the schema
- trace artifacts should identify first failure state and primary failure mode when a scenario fails

## Eval Baseline And Decision Artifacts

Baseline config path:

```text
<session-dir>/eval-artifacts/named-baselines.json
```

Decision artifact paths:

```text
<session-dir>/eval-artifacts/decision-artifacts/eval-comparison-<uuid>.json
<session-dir>/eval-artifacts/decision-artifacts/eval-promotion-<uuid>.json
```

Purpose:

- compare candidate harness behavior against named known-good eval runs
- prevent silent regressions before baseline promotion

Commands:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --set-eval-baseline main latest-pass:core
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --compare-eval-baseline main
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --auto-promote-eval-baseline main
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --audit-eval-baselines
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-decision-artifacts
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-decision-artifacts --decision-artifact-kind comparison
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-decision-artifacts --decision-artifact-kind promotion
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --review-eval-comparison
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --review-eval-promotion
```

Decision-artifact review behavior:

- `--review-eval-comparison` defaults to `latest-comparison`
- `--review-eval-promotion` defaults to `latest-promotion`
- both review commands also accept an exact path, full filename, or unique filename prefix
- `--decision-artifact-kind` can narrow both `--list-decision-artifacts` and `--prune-decision-artifacts` to `comparison` or `promotion`

Completion check:

- comparisons should report regressions, improvements, unchanged scenarios, and task-class rollups
- auto-promotion should not promote when regressions exist

## Minimum Reviewer Checklist

Before calling a harness milestone complete, inspect:

1. A session record with behavior IDs, BPE memory, validation, and final report.
2. A compact context artifact for that session.
3. A handoff artifact from a blocked or failed run.
4. A procedural repair record from a failed run.
5. An eval summary showing behavior IDs, BPE, repair IDs, and compact-context usage.
6. At least one trace artifact that validates against `trace-schema-v1.json`.
7. A baseline comparison or promotion decision artifact.

If those artifacts do not answer the reviewer questions above, the harness is not done.
