# Coding Agent V1

This is the implementation workspace for the first serious coding-agent build in this repo.

It follows the design in:

- `../v1-build-plan.md`
- `../v1-architecture.md`
- `../v1-task-breakdown.md`
- `../v1-demo-scenarios.md`

## Goal

Build a local repo-aware coding agent that can take a real coding task from request to verified code change with safe tool use and persistent session state.

## V1 Scope

The first implementation target is a small but complete local loop with:

- session entrypoint
- workspace context gathering
- core tool interfaces
- permission gate
- session memory
- validation and final reporting

## Package Layout

- `src/coding_agent_v1/cli.py`: CLI entrypoint
- `src/coding_agent_v1/models.py`: core dataclasses and enums
- `src/coding_agent_v1/behavior_index.py`: source-backed behavior map for core harness behaviors
- `src/coding_agent_v1/session_store.py`: session persistence
- `src/coding_agent_v1/workspace.py`: repo/workspace summary
- `src/coding_agent_v1/model_planner_adapter.py`: provider-agnostic model CLI adapter for `model_guided` planning
- `src/coding_agent_v1/tools.py`: tool definitions and interfaces
- `src/coding_agent_v1/permissions.py`: allow/ask/deny policy
- `src/coding_agent_v1/validator.py`: post-edit verification
- `src/coding_agent_v1/agent_loop.py`: main observe/inspect/choose/act/verify/report loop

## Reviewer Docs

- `docs/artifact-contract.md`: artifact schemas, paths, reviewer questions, and review commands
- `docs/flagship-demo-runbook.md`: end-to-end demo path for behavior-aware planning, BPE, compact resume, handoff, repair memory, evals, traces, and baselines
- `docs/flagship-demo-evidence-20260809.md`: concrete artifact bundle from the current flagship proof run
- `docs/model-guided-planner-gate.md`: implementation and eval gate for the next `model_guided` planner strategy
- `docs/milestone-summary.md`: requirement-by-requirement status, evidence, caveats, and next work

## Current State

This is no longer just a scaffold. The repo now has a working local harness with tests.

What exists now:

- workspace summary and repo-root detection
- persistent session records and event logs
- BPE-shaped working memory fields for belief, progress, and experience alongside compact continuation artifacts
- handoff artifacts for failed or stopped runs so later sessions can inspect the blocker and continuation state
- procedural repair records for approval, permission, and validation failures so repeated misses become reviewable candidate repairs
- real read/search/edit/command tools
- explicit and natural-language task-flow classification for inspect, fix, feature, rename, and diagnose requests with scored planner selection informed by workspace structure and test evidence
- explicit task plans that persist planner strategy, flow choice, feature strategy, initial actions, validation command, and planning reasons
- source-backed behavior-index evidence for core harness behaviors such as planning, validation selection, permissions, sessions, evals, baselines, and failure memory
- task-aware validation selection that can narrow feature and rename flows to matching test files from request text or module-aware workspace evidence, while preserving nested repo-relative test paths
- small feature support for explicit or inferred CLI flags, config-option defaults including inferred and natural-language option requests, and environment-variable-backed config entries including inferred and natural-language env-var requests
- workspace-bound permission decisions
- compact BPE continuation artifacts under `compactions/` that persist behavior ids, touched files, validation state, blocker state, and next-step hints without raw event history
- validation summaries and final reporting
- a repair loop for small failing-test cases
- proposal scoring and evidence capture for suggested fixes
- test coverage for the main harness behaviors
- a runnable external smoke eval benchmark pack with 5 scenarios, one per core task class
- a fully runnable external eval benchmark pack with 20 scenarios across fix, feature, rename, diagnose, and resume
- a runnable external stress eval benchmark pack with 5 harder scenarios covering ambiguity, approval boundaries, regression risk, and resume continuity
- a runnable external trace-oriented smoke pack for multi-step agent traces and tool-use review flows

What still needs to be built next:

- real LLM integration
- richer approval flow UX
- broader planner quality beyond the current scored evidence-based rules
- deeper behavior-guided planning beyond the first source-backed behavior index
- smarter validation selection beyond the current text-and-module matching rules
- compaction trigger metadata and eventual retention controls for very long sessions
- larger eval task sets for repeatable quality measurement

## Current Demonstrated Behaviors

The current harness can already demonstrate:

- read repo instructions like `README.md`
- require approval for risky actions unless auto-approved
- run `pytest -q` for test-oriented tasks
- inspect failure output and search related source files
- classify explicit and natural-language requests into inspect, fix, feature, rename, and diagnose flows with scored planner selection and workspace structure/test evidence before acting
- persist an explicit task plan with a chosen validation command before acting
- narrow feature and rename validation to matching test files when request text or module structure makes the target clear, including nested repo-relative test paths
- repair simple arithmetic, literal-return, and constant-return bugs
- add a small explicit or inferred argparse CLI flag feature, explicit or inferred config option default, or explicit, inferred, or natural-language environment-variable-backed config entry
- perform safe multi-file renames using exact symbol matches
- support a diagnose-only flow that gathers failure evidence without applying edits
- review and resume saved sessions
- carry compact BPE continuation state across resumed sessions when a compaction artifact is available
- write handoff artifacts under `handoffs/` when approval stops a run or validation remains failed
- write and recall candidate procedural repair records under `repair-records/` for later matching task flows
- run a built-in fixed eval suite across task success, natural-language bug-intent routing, natural-language feature requests, approval gating, and resume flow
- run the external `coding-agent-v1` smoke eval pack as a small external benchmark tier
- run the external `coding-agent-v1` core eval pack as the default benchmark path
- run the external `coding-agent-v1` stress eval pack as a focused harder benchmark tier
- run the external `coding-agent-v1` trace-oriented smoke pack as a small agent-trace benchmark tier
- persist eval summaries as JSON artifacts with timestamps, labels, timing, and outcome reasons
- report BPE memory and compact-context usage in eval summaries and trace artifacts
- list saved eval artifacts by date, label, and pass rate
- resolve saved eval artifacts by label for compare and history workflows
- support aliases like `latest`, `latest-pass`, and `latest:<prefix>` for eval selection
- store named baselines like `main`, `release`, or `golden` for stable eval references
- promote a resolved artifact into a named baseline in one step
- compare a named baseline against `latest-pass` or another resolved reference in one step
- auto-promote a candidate into a baseline only when comparison shows no regressions
- compare saved eval artifacts for regressions and improvements
- persist comparison and auto-promotion decisions as JSON artifacts for later audit
- summarize scenario trends across multiple eval artifacts
- carry scenario pack ids through saved eval listings, history summaries, and comparisons
- print task-class and failure-mode rollups for eval runs and task-class regression rollups for eval comparisons
- rerun validation and summarize the final result

As of Sunday, August 9, 2026, the local harness suite passes with:

- `298 passed`

## Immediate Next Steps

1. Add harder planner-quality scenarios where `model_guided` must improve planning choices, not only match `deterministic_heuristic`.
2. Keep `deterministic_heuristic` as the default until model-guided runs prove stable improvement across those harder packs.
3. Add eval scenarios for very long sessions and compaction-trigger reporting.
4. Improve validation command selection beyond the current text-and-module matching rules.

## Eval Commands

From `projects/coding-agent-v1/`:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-evals
```

This now runs the external `coding-agent-v1` core benchmark pack by default.

For the external smoke-tier pack:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-eval-pack ../../evals/coding-agent-v1/scenarios/smoke-v1.json
```

For the external stress-tier pack:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-eval-pack ../../evals/coding-agent-v1/scenarios/stress-v1.json
```

For the external trace-oriented smoke pack:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-eval-pack ../../evals/agent-evals/scenarios/coding-agent-v1-smoke-v1.json
```

For the older built-in smoke suite:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-smoke-evals
```

Saved eval references now support pack-aware aliases as well, so comparisons and history queries can target benchmark tiers directly:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --compare-evals latest-pass:core latest-pass:stress
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --history-evals latest:built-in latest:smoke latest:trace-smoke latest:stress
```

For direct filtering on saved artifact listings and history views:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-evals --eval-pack-filter smoke
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --history-evals latest:built-in latest:smoke latest:trace-smoke latest:stress --eval-pack-filter stress
```

Pack-aware selectors now also recognize `agent-smoke`, `trace-smoke`, and `agent-evals-smoke` for the external trace-oriented pack.

Named baselines can also be pack-scoped on resolution:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --compare-evals baseline:main:core latest-pass:core
```

For `--compare-eval-baseline` or `--auto-promote-eval-baseline`, the default candidate is still `latest-pass`, scoped to the saved baseline's scenario pack. Use `latest-clean[:PACK]` when expectation checks must also be clean.

`--list-eval-baselines` also now surfaces baseline status, scenario pack id, run label, and pass metadata, and it marks missing artifact targets explicitly.

Missing baseline targets can also be repaired directly:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --repair-eval-baseline main
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --repair-eval-baseline main latest-pass:stress
```

If no explicit repair reference is provided, the command prefers `latest-clean` within the saved baseline's own scenario pack, then falls back to `latest-pass` when no clean candidate exists.

For a read-only baseline drift scan:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --audit-eval-baselines
```

The audit reports whether each baseline is `current`, `stale`, `missing`, or `missing-no-candidate`, and when available it prints the recommended same-pack `latest-clean:<pack>` reference, falling back to `latest-pass:<pack>` only when no clean candidate exists.

Saved handoff artifacts can be reviewed by source session id:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --review-handoff <session-id>
```

Compact BPE continuation artifacts can also be reviewed by source session id:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --review-compact-context <session-id>
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-compact-contexts
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-compact-contexts --prune-compact-keep-newest 20
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-compact-contexts --prune-compact-contexts-apply
```

Compact pruning is dry-run by default. It keeps the newest artifacts and protects `size_triggered:*` compactions unless `--prune-compact-include-size-triggered` is provided.

And a new run can resume directly from a handoff artifact:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --resume-handoff <session-id> "continue the task"
```

Candidate procedural repair records can also be listed and reviewed:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-repair-records
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --review-repair-record <repair-id>
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --set-repair-record-status <repair-id> accepted --repair-status-reason "validated repeated fix"
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-repair-status-audits <repair-id>
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --review-repair-status-audit <audit-id>
```

Allowed repair statuses are `candidate`, `accepted`, `rejected`, and `retired`. This keeps failure memory reviewable: the harness may create candidates automatically, but a human or policy gate can promote or retire them explicitly, with an audit artifact recording each transition.

For safe eval-summary retention cleanup:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-evals
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-evals --prune-evals-apply
```

The prune flow is dry-run by default. It currently prunes only `eval-summary-*.json` artifacts, while protecting named baseline targets and keeping the newest and newest-passing artifacts per pack based on `--prune-keep-per-pack`.

For safe cleanup of saved decision artifacts:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-decision-artifacts
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-decision-artifacts --prune-decision-artifacts-apply
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-decision-artifacts --prune-decision-keep-per-kind 2 --prune-keep-per-pack 3
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-decision-artifacts --decision-artifact-kind promotion
```

This flow is also dry-run by default. It currently targets `decision-artifacts/eval-comparison-*.json` and `decision-artifacts/eval-promotion-*.json`, protects the newest artifacts per decision kind based on `--prune-decision-keep-per-kind`, and also protects decision artifacts that still reference retained eval-summary artifacts. Decision-artifact recency is determined from the saved `created_at` timestamp when present, with filename order used only as a fallback for older artifacts that do not include that field. `--decision-artifact-kind` can now scope both listing and pruning to `comparison` or `promotion`.

For decision-artifact discovery and review:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-decision-artifacts
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-decision-artifacts --decision-artifact-kind promotion
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --review-eval-comparison
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --review-eval-promotion
```

`--review-eval-comparison` now defaults to `latest-comparison`, and `--review-eval-promotion` now defaults to `latest-promotion`, so the newest saved decision artifact of the matching kind can be inspected without first copying a path. If you need a specific artifact, both review commands also accept an exact path, a full filename, or a unique filename prefix.
