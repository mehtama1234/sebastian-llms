# Flagship Demo Runbook

This runbook shows the end-to-end harness story for `coding-agent-v1`.

It is written for review, not for a polished product demo. The goal is to prove the harness can explain, persist, resume, learn from, and evaluate a coding-agent run.

## Demo Claim

The harness can handle a realistic validation-selection improvement path:

```text
Improve validation selection so rename tasks choose the right targeted test even when the old symbol is not mentioned in the test file.
```

The current implementation proves this through behavior-aware planning, module-aware rename validation, BPE memory, compact resume, failure handoff, procedural repair records, eval traces, and baseline comparison.

## Setup

Run from:

```bash
cd projects/coding-agent-v1
```

Use a clean demo artifact directory:

```bash
rm -rf .coding-agent-v1/demo-sessions
mkdir -p .coding-agent-v1/demo-sessions
```

## 1. Prove Behavior-Aware Planning

Run a request against this repo:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --cwd . \
  "improve validation selection for rename tasks"
```

Expected evidence:

- output includes a `session_id`
- session review shows `validation_selection` in task-plan behavior IDs
- session review shows implementation surfaces such as agent loop, planner, eval harness, or tests

Review:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --review-session <session-id>
```

Reviewer check:

- `task_plan:` includes `behaviors=...validation_selection`
- `task_plan:` includes source-backed `surfaces=...`
- `working_memory_belief:` and `working_memory_progress:` are present

## 2. Prove Compact BPE Continuation

Review the compact continuation artifact for the same session:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --review-compact-context <session-id>
```

Expected evidence:

- `compact_session_id: <session-id>`
- `affected_behaviors: ...`
- `belief: ...`
- `progress: ...`
- `next_step: ...`
- `summary: ...`

Resume from the session:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --cwd . \
  --resume-session <session-id> \
  "summarize this repo again"
```

Expected evidence:

- new output includes `resumed_from: <session-id>`
- the new session review includes compact-resume evidence in events or experience

## 3. Prove Handoff On Blocked Execution

Run a command-oriented request without auto-approval:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --cwd . \
  "run the tests"
```

Expected evidence:

- status is `failed`
- final report says approval is required
- a handoff artifact is written
- a candidate procedural repair record is written

Review handoff:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --review-handoff <failed-session-id>
```

Reviewer check:

- `reason: approval_required`
- `belief:` is present
- `progress:` is present
- `blocker:` is present
- `next_step:` is present

Resume from handoff:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --cwd . \
  --resume-handoff <failed-session-id> \
  "continue by summarizing this repo"
```

Expected evidence:

- new output includes `resumed_from: <failed-session-id>`
- new session review carries handoff BPE state in `working_memory_experience`

## 4. Prove Procedural Repair Memory

List repair records:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --list-repair-records
```

Review one repair:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --review-repair-record <repair-id>
```

Expected evidence:

- `failure_pattern:` is present
- `recommended_recovery:` is present
- `affected_behaviors:` is present when behavior-index evidence exists
- `status: candidate`

Reviewer check:

- repair memory is reviewable and bounded
- the harness does not silently auto-promote repair rules

## 5. Prove Module-Aware Rename Validation

Run the external core eval pack:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --run-eval-pack ../../evals/coding-agent-v1/scenarios/core-v1.json \
  --eval-label demo-core
```

Expected evidence:

- summary says `scenario_pack_id: coding-agent-v1-core`
- summary says `passed: 20`
- `rename-002`, `rename-003`, or another rename scenario passes
- summary includes `behavior_ids=...validation_selection`
- resume scenarios include `compact_context=true`
- summary includes task-class and failure-mode rollups

## 6. Prove Trace Artifacts

Run the trace-oriented smoke pack:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --run-eval-pack ../../evals/agent-evals/scenarios/coding-agent-v1-smoke-v1.json \
  --eval-label demo-agent-evals-smoke
```

Expected evidence:

- each eval result has a `trace_artifact_path`
- traces include `harness_state`
- traces include `harness_state.planner_strategy`
- traces include `harness_state.behavior_ids`
- traces include `harness_state.has_bpe_memory`
- traces include `harness_state.used_compact_context`
- traces include `harness_state.compaction_trigger`
- traces include `expectation_checks`

## 7. Prove Baseline Comparison

Set a baseline from a passing core run:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --set-eval-baseline main latest-pass:core
```

Run the core pack again:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --run-eval-pack ../../evals/coding-agent-v1/scenarios/core-v1.json \
  --eval-label demo-core-candidate
```

Compare:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --compare-eval-baseline main
```

Expected evidence:

- output includes `regressions: 0`
- output includes `baseline_scenario_pack_id: coding-agent-v1-core`
- output includes `candidate_scenario_pack_id: coding-agent-v1-core`
- output includes `task_class_comparison_summary`

Optional guarded promotion:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/demo-sessions \
  --auto-promote-eval-baseline main
```

Expected evidence:

- promotion succeeds only if comparison has no regressions
- a decision artifact is written

## Final Reviewer Checklist

The demo is successful when a reviewer can point to artifacts proving:

1. `validation_selection` was selected as an affected behavior.
2. The task plan listed concrete implementation surfaces.
3. Session records contain BPE working memory.
4. Compact context artifacts exist and are used during resume.
5. Blocked runs write handoff artifacts.
6. Failure paths write candidate repair records.
7. Eval summaries show behavior IDs, BPE memory, repair IDs where applicable, and compact-context usage.
8. Trace artifacts validate against the trace schema.
9. Baseline comparison reports whether the candidate regressed.

If any of these cannot be shown from files or CLI output, the harness milestone is incomplete.
