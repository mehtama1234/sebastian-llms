# Model-Guided Planner Gate

## Purpose

`model_guided` planning is the next implementation layer for `coding-agent-v1`.

The goal is not to replace the deterministic planner with an opaque model call. The goal is to add a model-backed planner behind the existing `TaskPlan` contract and prove it is at least as safe, inspectable, and measurable as the deterministic baseline.

## Current State

The harness already has the required extension points:

- `planner.py` defines `deterministic_heuristic` as the default planner strategy.
- `planner.py` recognizes `model_guided` and validates model-planner configuration.
- `planner.py` exposes a `PlannerBackend` boundary and `PlannerConfigurationError` for pre-action strategy failures.
- `agent_loop.py` can execute the configured model planner command as a subprocess.
- CLI accepts `--planner-strategy`.
- eval scenario specs can declare `planner_strategy`.
- eval summaries persist `planner_strategy`.
- trace artifacts persist `harness_state.planner_strategy`.
- baseline comparison can compare runs from the same scenario pack.

So the implementation should use the existing strategy boundary instead of creating a parallel planning path.

## Implementation Goal

Implement `model_guided` as an eval-gated planner strategy that can produce the same stable `TaskPlan` shape as `deterministic_heuristic`:

- `task_flow`
- `planner_strategy`
- `planner_strategy_reason`
- `affected_behavior_ids`
- `implementation_surfaces`
- `initial_actions`
- `validation_command`
- `validation_reason`
- `feature_strategy`
- `reasons`
- `candidates`

The model may help choose or explain the plan, but the harness remains responsible for validation, bounds, artifact persistence, and fallback.

## Subprocess Contract

`model_guided` uses the command in:

```text
CODING_AGENT_V1_MODEL_PLANNER_COMMAND
```

The command is executed with `shlex.split(...)`, receives one JSON object on stdin, and must write one JSON object to stdout.

The repo includes a provider-agnostic adapter:

```bash
coding-agent-v1-model-planner-adapter
```

Typical wiring:

```bash
export CODING_AGENT_V1_MODEL_PLANNER_COMMAND="coding-agent-v1-model-planner-adapter"
export CODING_AGENT_V1_MODEL_COMMAND="<your model CLI command>"
```

The adapter sends a constrained planner prompt to `CODING_AGENT_V1_MODEL_COMMAND`, extracts the model's JSON object from stdout, validates it, and prints the normalized planner decision required by the harness.

Input fields:

- `request`
- `workspace_root`
- `instruction_files`
- `deterministic_baseline`
- `contract`

The deterministic baseline includes the current deterministic `TaskPlan` fields so the model can compare against the safe planner.

Required output fields:

- `task_flow`: one of `inspect`, `fix`, `feature`, `rename`, `diagnose`, or `resume`
- `reasons`: non-empty string or list of strings explaining the planner decision

Optional output fields:

- `feature_strategy`
- `feature_arguments`

The harness intentionally recomputes:

- behavior IDs
- implementation surfaces
- validation command
- initial actions

That keeps model output bounded to planner decision evidence instead of letting the model bypass harness safety and artifact contracts.

## Required Behavior

### 1. Deterministic Baseline Remains Default

`deterministic_heuristic` must stay the default planner strategy.

`model_guided` must be opt-in through:

```bash
python -m coding_agent_v1.cli --planner-strategy model_guided "request text"
```

or through an eval scenario with:

```json
"planner_strategy": "model_guided"
```

### 2. Stable Planner Contract

The model-backed planner must return a normal `TaskPlan`.

It must not bypass:

- behavior-index lookup
- workspace-bound implementation surfaces
- permission policy
- validation selection
- session persistence
- eval trace generation

### 3. Safe Fallback

If the model planner cannot produce a valid plan, the harness must either:

- fail loudly with a planner error before taking action, or
- fall back to `deterministic_heuristic` and record the fallback reason in `planner_strategy_reason`.

Silent fallback is not acceptable because reviewers need to know which planner actually made the decision.

### 4. Reviewable Model Evidence

A model-guided plan must record enough evidence for a reviewer to inspect the decision:

- selected strategy: `model_guided`
- model planner reason
- deterministic baseline flow if computed
- model-selected flow
- behavior IDs used
- implementation surfaces used
- validation command and reason
- fallback reason if fallback happened

No raw chain-of-thought is required. The artifact should contain concise decision evidence, not hidden reasoning.

### 5. Eval Gate Before Default Use

`model_guided` cannot become default until it passes a planner-quality eval gate.

Minimum gate:

- run deterministic baseline on planner-quality pack
- run model-guided candidate on the same pack
- compare candidate against baseline
- require `regressions: 0`
- require `expectation_regressions: 0`
- require no new tool-sequence misses
- require no new escalation mismatches
- require every trace to include `harness_state.planner_strategy=model_guided` or an explicit fallback reason

The same pack can be reused for candidate runs with:

```bash
PYTHONPATH=src python3 -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/planner-quality-gate-check \
  --run-eval-pack ../../evals/coding-agent-v1/scenarios/planner-quality-v1.json \
  --eval-planner-strategy model_guided \
  --eval-label planner-quality-model-guided-candidate
```

The preferred repeatable gate command is:

```bash
scripts/run_planner_quality_gate.sh
```

It runs the deterministic baseline, runs the model-guided candidate, compares them, and exits nonzero if `regressions` or `expectation_regressions` are not `0`.

## Planner-Quality Eval Pack

Use the dedicated scenario pack:

```text
evals/coding-agent-v1/scenarios/planner-quality-v1.json
```

It includes scenarios that pressure the planner, not just the edit loop:

- passive failure report that should become `diagnose`
- explicit failing-test repair that should become `fix`
- feature request with explicit config or CLI flag target
- rename request with module-aware validation
- resume request that should use prior compact context
- permission-boundary task that must preserve escalation behavior
- failure-memory task that should identify `failure_memory`

The current external eval schema supports `fix`, `feature`, `rename`, `diagnose`, and `resume`. It does not yet support standalone `inspect` scenarios, so inspect-only planner pressure should be added in a later schema expansion.

Current deterministic baseline check:

```bash
PYTHONPATH=src python3 -m coding_agent_v1.cli \
  --session-dir .coding-agent-v1/planner-quality-contract-check \
  --run-eval-pack ../../evals/coding-agent-v1/scenarios/planner-quality-v1.json \
  --eval-label planner-quality-contract-check
```

Result:

- `scenario_pack_id: coding-agent-v1-planner-quality`
- `passed: 10`
- `failed: 0`
- `trace_count: 10`
- `tool_sequence_match: 10/10`
- `escalation_match: 10/10`
- artifact: `.coding-agent-v1/planner-quality-contract-check/eval-artifacts/eval-summary-6014cbaafcb34715ac991c4f5e2e957f.json`

Current configured-subprocess smoke check:

- CLI run with a temporary `CODING_AGENT_V1_MODEL_PLANNER_COMMAND` completed successfully.
- saved session persisted `planner_strategy=model_guided`.
- saved session recorded the model planner reason and deterministic baseline task flow.

Current planner-quality gate check:

- artifact root: `.coding-agent-v1/planner-quality-codex-gate-20260809-182449/`
- deterministic baseline: `eval-summary-04b3e978ba694a169a8400b5d20a4759.json`
- model-guided candidate: `eval-summary-662e5d433b5d4f1ebb0337e0f801bedb.json`
- comparison artifact: `eval-comparison-e05cd79bb89c4981adfa7dc9ad58f957.json`
- model command: `codex exec --sandbox read-only --skip-git-repo-check --ephemeral -`
- baseline passed: `10/10`
- candidate passed: `10/10`
- regressions: `0`
- expectation regressions: `0`
- tool sequence: baseline `10/10`, candidate `10/10`
- escalation: baseline `10/10`, candidate `10/10`
- verified through `scripts/run_planner_quality_gate.sh`

Current planner-superiority gate check:

- pack: `../../evals/coding-agent-v1/scenarios/planner-quality-v2.json`
- gate script: `scripts/run_planner_superiority_gate.sh`
- artifact root: `.coding-agent-v1/planner-superiority-codex-gate-20260809-185700/`
- deterministic baseline: `eval-summary-f1c21d2d53e34807b9d250794ffd1541.json`
- model-guided candidate: `eval-summary-df3cbe3f7fdc480996bb0267324e869f.json`
- comparison artifact: `eval-comparison-c532618da4924541908d06c41a007c7c.json`
- baseline passed: `6/10`
- candidate passed: `6/10`
- regressions: `0`
- expectation regressions: `0`
- improvements: `0`
- result: gate failed because `PLANNER_SUPERIORITY_MIN_IMPROVEMENTS` defaults to `1`

Interpretation:

- The Codex-backed planner path remains parity-safe on the harder v2 pack.
- It has not yet shown pass/fail superiority over the deterministic planner.
- `model_guided` must stay opt-in until the planner or executor contract changes enough to create real improvements on v2.

Each scenario should declare:

- expected task class
- expected behavior IDs through existing trace or result requirements where possible
- expected tool sequence
- expected escalation behavior
- planner strategy under test

## Acceptance Criteria

This milestone is done when:

1. `--planner-strategy model_guided` accepts configured subprocess output that validates against the planner contract.
2. Missing model configuration fails before any tool action and records a clear planner error.
3. `deterministic_heuristic` remains the default and existing deterministic tests still pass.
4. model-guided plans persist through session records, eval summaries, and trace artifacts.
5. planner-quality eval pack exists and runs for deterministic baseline.
6. planner-quality eval pack runs for model-guided candidate.
7. baseline comparison reports `0` regressions and `0` expectation regressions before any default change.
8. docs and reviewer evidence are regenerated after the gate passes.

## Non-Goals

This milestone does not include:

- autonomous self-editing without review
- subagent delegation
- reinforcement learning
- model-ranked long-term memory
- making `model_guided` the default before eval proof

## First Coding Slice

The first implementation slice is now in place:

1. `PlannerBackend` boundary exists.
2. `deterministic_heuristic` remains the default backend.
3. `model_guided` validates `CODING_AGENT_V1_MODEL_PLANNER_COMMAND`.
4. missing model configuration fails before actions.
5. configured model planner commands receive baseline JSON on stdin.
6. invalid model planner JSON fails before actions.
7. valid model planner JSON produces a normal `TaskPlan`.
8. eval scenario packs can run `planner_strategy=model_guided`.
9. `planner-quality-v1.json` runs as the deterministic baseline.
10. provider-agnostic model planner adapter exists as `coding-agent-v1-model-planner-adapter`.

Next coding slice:

1. Inspect the four shared v2 failures: `planner-v2-feature-002`, `planner-v2-rename-001`, `planner-v2-approval-001`, and `planner-v2-resume-001`.
2. Decide whether those failures belong in planner selection, executor behavior, or scenario expectations.
3. Improve the model-guided planner contract only where it can affect execution, not merely rewrite reasons.
4. Rerun `scripts/run_planner_superiority_gate.sh` and require at least one improvement with zero regressions before any default change.
