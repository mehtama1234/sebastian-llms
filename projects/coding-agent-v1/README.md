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
- `src/coding_agent_v1/session_store.py`: session persistence
- `src/coding_agent_v1/workspace.py`: repo/workspace summary
- `src/coding_agent_v1/tools.py`: tool definitions and interfaces
- `src/coding_agent_v1/permissions.py`: allow/ask/deny policy
- `src/coding_agent_v1/validator.py`: post-edit verification
- `src/coding_agent_v1/agent_loop.py`: main observe/inspect/choose/act/verify/report loop

## Current State

This is no longer just a scaffold. The repo now has a working local harness with tests.

What exists now:

- workspace summary and repo-root detection
- persistent session records and event logs
- real read/search/edit/command tools
- explicit and natural-language task-flow classification for inspect, fix, feature, rename, and diagnose requests with scored planner selection informed by workspace structure and test evidence
- explicit task plans that persist flow choice, feature strategy, initial actions, validation command, and planning reasons
- task-aware validation selection that can narrow feature and rename flows to matching test files from request text or module-aware workspace evidence, while preserving nested repo-relative test paths
- small feature support for explicit or inferred CLI flags, config-option defaults including inferred and natural-language option requests, and environment-variable-backed config entries including inferred and natural-language env-var requests
- workspace-bound permission decisions
- compact working-memory snapshots that persist focus, touched files, validation state, and next-step hints
- validation summaries and final reporting
- a repair loop for small failing-test cases
- proposal scoring and evidence capture for suggested fixes
- test coverage for the main harness behaviors
- a runnable external smoke eval benchmark pack with 5 scenarios, one per core task class
- a fully runnable external eval benchmark pack with 20 scenarios across fix, feature, rename, diagnose, and resume
- a runnable external stress eval benchmark pack with 5 harder scenarios covering ambiguity, approval boundaries, regression risk, and resume continuity

What still needs to be built next:

- real LLM integration
- richer approval flow UX
- broader planner quality beyond the current scored evidence-based rules
- smarter validation selection beyond the current text-and-module matching rules
- deeper long-session memory compression beyond the current compact snapshot
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
- carry a compact working-memory snapshot across resumed sessions
- run a built-in fixed eval suite across task success, natural-language bug-intent routing, natural-language feature requests, approval gating, and resume flow
- run the external `coding-agent-v1` smoke eval pack as a small external benchmark tier
- run the external `coding-agent-v1` core eval pack as the default benchmark path
- run the external `coding-agent-v1` stress eval pack as a focused harder benchmark tier
- persist eval summaries as JSON artifacts with timestamps, labels, timing, and outcome reasons
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

As of Sunday, August 9, 2026, the local test suite passes with:

- `123 passed`

## Immediate Next Steps

1. Add a real model-backed planner that improves on the current scored evidence-based rules.
2. Expand the session model into resumable memory plus compact working summaries.
3. Expand the eval harness beyond the current core external pack with more scenario packs and richer regression slicing across each task flow.
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

For the older built-in smoke suite:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-smoke-evals
```

Saved eval references now support pack-aware aliases as well, so comparisons and history queries can target benchmark tiers directly:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --compare-evals latest-pass:core latest-pass:stress
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --history-evals latest:built-in latest:smoke latest:stress
```

For direct filtering on saved artifact listings and history views:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-evals --eval-pack-filter smoke
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --history-evals latest:built-in latest:smoke latest:stress --eval-pack-filter stress
```

Named baselines can also be pack-scoped on resolution:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --compare-evals baseline:main:core latest-pass:core
```

And for `--compare-eval-baseline` or `--auto-promote-eval-baseline`, the default `latest-pass` candidate now stays within the saved baseline's scenario pack when that baseline already points at a known pack tier.

`--list-eval-baselines` also now surfaces baseline status, scenario pack id, run label, and pass metadata, and it marks missing artifact targets explicitly.

Missing baseline targets can also be repaired directly:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --repair-eval-baseline main
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --repair-eval-baseline main latest-pass:stress
```

If no explicit repair reference is provided, the command defaults to `latest-pass` within the saved baseline's own scenario pack when that metadata is available.

For a read-only baseline drift scan:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --audit-eval-baselines
```

The audit reports whether each baseline is `current`, `stale`, `missing`, or `missing-no-candidate`, and when available it prints the recommended same-pack `latest-pass:<pack>` reference and artifact path.

For safe eval-summary retention cleanup:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-evals
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-evals --prune-evals-apply
```

The prune flow is dry-run by default. It currently prunes only `eval-summary-*.json` artifacts, while protecting named baseline targets and keeping the newest and newest-passing artifacts per pack based on `--prune-keep-per-pack`.
