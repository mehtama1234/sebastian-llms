# Coding Agent V1 Evals

This directory is the external eval-lab workspace for `projects/coding-agent-v1/`.

Its purpose is to separate three things that were previously mixed together:

- the current in-code smoke eval suite used for regression checks inside the package
- the broader scenario catalog we want to grow into a serious benchmark set
- the rubric language for how failures should be classified and compared

## Scope

This eval track is for measuring the minimum task classes that matter for a repo-aware coding agent:

- `fix`
- `feature`
- `rename`
- `diagnose`
- `resume`

The external catalog should eventually be the source of truth for a broader benchmark set, while the built-in in-package suite remains a fast local regression pack.

## Current Files

- `scenarios/smoke-v1.json`: fast external smoke pack with one runnable scenario per core task class
- `scenarios/core-v1.json`: first external scenario catalog with 20 tasks across the 5 core task classes
- `scenarios/stress-v1.json`: focused external stress pack for ambiguity, approval boundaries, regression risk, and resume robustness
- `scenarios/planner-quality-v1.json`: planner-focused pack for deterministic versus future model-guided planner comparisons
- `scenarios/planner-quality-v2.json`: harder planner-superiority pack where model-guided planning must beat deterministic planning before any default switch
- `../agent-evals/scenarios/coding-agent-v1-smoke-v1.json`: trace-oriented smoke pack for multi-step agent traces and tool-use review flows
- `rubrics.md`: scoring language and failure taxonomy for scenario outcomes

## Current Execution Path

The external core pack is fully runnable through the package CLI and remains the default broader benchmark path.

From `projects/coding-agent-v1/`, run:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-eval-pack
```

Or point at an explicit pack:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-eval-pack ../../evals/coding-agent-v1/scenarios/core-v1.json
```

For the smaller external smoke-tier pack, run:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-eval-pack ../../evals/coding-agent-v1/scenarios/smoke-v1.json
```

For the focused external stress-tier pack, run:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-eval-pack ../../evals/coding-agent-v1/scenarios/stress-v1.json
```

For the planner-quality pack, run:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-eval-pack ../../evals/coding-agent-v1/scenarios/planner-quality-v1.json
```

To run the same pack as a model-guided candidate without editing the pack JSON:

```bash
python -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/sessions \
  --run-eval-pack ../../evals/coding-agent-v1/scenarios/planner-quality-v1.json \
  --eval-planner-strategy model_guided \
  --eval-label planner-quality-model-guided-candidate
```

From `projects/coding-agent-v1/`, the full deterministic-vs-model-guided gate is:

```bash
scripts/run_planner_quality_gate.sh
```

The script requires `CODING_AGENT_V1_MODEL_PLANNER_COMMAND`, runs both evals into one artifact directory, compares the candidate against the baseline, and fails if either regressions or expectation regressions are nonzero.

For the harder planner-superiority pack, run:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-eval-pack ../../evals/coding-agent-v1/scenarios/planner-quality-v2.json
```

From `projects/coding-agent-v1/`, the deterministic-vs-model-guided superiority gate is:

```bash
scripts/run_planner_superiority_gate.sh
```

The superiority gate requires the same model planner command configuration as the v1 gate. It fails on any regression, any expectation regression, or fewer than `PLANNER_SUPERIORITY_MIN_IMPROVEMENTS` pass/fail improvements. The default minimum is `1`.

Current Codex-backed v2 result:

- artifact root: `.coding-agent-v1/planner-superiority-codex-gate-20260809-185700/`
- deterministic baseline: `6/10`
- model-guided candidate: `6/10`
- regressions: `0`
- expectation regressions: `0`
- improvements: `0`
- result: gate failed, so `model_guided` is not default-ready

For the external trace-oriented smoke pack, run:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-eval-pack ../../evals/agent-evals/scenarios/coding-agent-v1-smoke-v1.json
```

This writes the usual eval artifact under `.coding-agent-v1/sessions/eval-artifacts/` and prints:

- the normal eval summary
- a task-class breakdown
- a failure-mode breakdown
- the scenario pack id for the run

Saved comparisons now also print baseline and candidate scenario pack ids plus a task-class comparison summary in addition to scenario-level regression lines.

Saved artifact listings and history summaries now also surface scenario pack ids so multi-run review can answer whether results came from the built-in suite, the external smoke tier, the trace-oriented smoke tier, the broader core tier, or the focused stress tier.

For direct CLI filtering on those views, use `--eval-pack-filter` with `--list-evals` or `--history-evals`. Examples:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --list-evals --eval-pack-filter stress
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --history-evals latest:built-in latest:smoke latest:trace-smoke latest:stress --eval-pack-filter stress
```

Artifact resolution now also supports pack-aware aliases. Examples:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --compare-evals latest-pass:smoke latest-pass:stress
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --history-evals latest:built-in latest:smoke latest:trace-smoke latest:stress
```

For `latest:<selector>` and `latest-pass:<selector>`, the selector can be:

- a scenario-pack tier alias like `built-in`, `smoke`, `agent-smoke`, `trace-smoke`, `core`, `stress`, `planner`, `planner-quality`, `planner-v2`, or `planner-superiority`
- an exact scenario pack id like `coding-agent-v1-stress`
- or an older run-label prefix, which still works when the selector is not recognized as a pack tier

Named baselines can now also be resolved with a pack selector:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --compare-evals baseline:main:core latest-pass:core
```

For existing named baselines, `--compare-eval-baseline` and `--auto-promote-eval-baseline` default `latest-pass` to the same scenario pack as the saved baseline artifact. Use `latest-clean[:PACK]` when expectation checks must also be clean.

`--list-eval-baselines` now also shows per-baseline status, scenario pack id, run label, and pass metadata, and it flags baseline targets whose artifact file is missing.

When a baseline target is missing, you can now repair it directly:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --repair-eval-baseline main
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --repair-eval-baseline main latest-pass:core
```

With no explicit reference, repair prefers `latest-clean` within the saved baseline's own scenario pack when that pack id is known, then falls back to `latest-pass` when no clean candidate exists.

For a read-only scan across all baselines, use:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --audit-eval-baselines
```

This reports whether each baseline is `current`, `stale`, `missing`, or `missing-no-candidate`, and when possible it shows the recommended same-pack `latest-clean:<pack>` reference, falling back to `latest-pass:<pack>` when no clean candidate exists.

For safe eval-summary cleanup, use:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-evals
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-evals --prune-evals-apply
```

The prune plan is dry-run by default. It currently targets `eval-summary-*.json` artifacts, protects named baseline targets, and retains the newest and newest-passing artifacts per scenario pack according to `--prune-keep-per-pack`.

For safe cleanup of saved comparison and promotion decisions, use:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-decision-artifacts
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-decision-artifacts --prune-decision-artifacts-apply
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --prune-decision-artifacts --prune-decision-keep-per-kind 2 --prune-keep-per-pack 3
```

This plan is also dry-run by default. It currently targets `decision-artifacts/eval-comparison-*.json` and `decision-artifacts/eval-promotion-*.json`, retains the newest artifacts per decision kind with `--prune-decision-keep-per-kind`, and protects decision artifacts that still reference eval-summary artifacts retained by the eval-summary prune policy. Recency is determined from the artifact `created_at` timestamp when available, with filename order used only as a fallback for older decision artifacts that do not store that field.

For the older built-in smoke suite, use:

```bash
python -m coding_agent_v1.cli --session-dir .coding-agent-v1/sessions --run-smoke-evals
```

That built-in suite is still the fastest in-package regression check. `smoke-v1.json` is the small external benchmark tier, `coding-agent-v1-smoke-v1.json` is the trace-oriented smoke tier for multi-step agent flows, `core-v1.json` is the broader balanced benchmark tier, and `stress-v1.json` is the curated harder pack for safety and continuity edge cases.

## Design Position

The existing package evals already support:

- run artifacts
- comparisons
- named baselines
- guarded promotion
- history summaries

What they do not yet provide is a durable external task catalog with:

- broader task coverage
- clear task-class balancing
- explicit failure-mode expectations
- a stable place to add new benchmark scenarios without expanding hard-coded lists

This folder is now the first executable version of that layer, not just a planning stub.
