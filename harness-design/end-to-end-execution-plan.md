# End-To-End Execution Plan

This file converts `harness-design/end-to-end-goal.md` into a practical build sequence for `projects/coding-agent-v1/`.

It assumes the current state is:

- core loop exists
- safety exists
- session persistence exists
- eval harness exists
- behavior-indexed planning exists
- BPE working memory exists
- handoff and resume artifacts exist
- compact continuation artifacts exist
- procedural repair records exist
- trace artifacts and baseline comparisons exist
- `model_guided` planning is implemented as an opt-in subprocess-backed planner
- a Codex-backed planner-quality gate has passed with parity against the deterministic baseline

## Implementation Strategy

Do not restart the project.

Do not jump to subagents.

Do not spend the next phase on random feature additions.

Instead, finish the missing load-bearing layers in this order:

1. keep the deterministic planner as the baseline contract
2. keep `model_guided` opt-in until harder evals show it improves planning quality
3. expand eval pressure around planner quality, resume quality, and validation selection
4. harden artifact retention and review surfaces

That sequence keeps the work aligned with the harness-design material and with the current codebase.

## Current Flagship Proof State

The project has already reached the first serious harness endpoint:

- behavior-aware task plans include planner strategy, behavior IDs, implementation surfaces, validation command, and rationale
- sessions persist BPE working memory, events, validation results, touched files, and final reports
- compact continuation artifacts preserve useful state with compaction trigger metadata
- approval-boundary failures write handoff artifacts and candidate procedural repair records
- later runs can resume from compact context or handoff artifacts
- eval summaries and trace artifacts expose planner strategy, BPE memory, compact-context use, repair IDs, tool sequence, escalation behavior, and compaction trigger
- baseline comparison reports regressions and expectation regressions

Current reviewer evidence:

- artifact bundle: `projects/coding-agent-v1/.coding-agent-v1/demo-sessions-20260809-173926/`
- core eval: `20/20`
- trace-oriented smoke eval: `5/5`
- baseline comparison: `0` regressions and `0` expectation regressions
- `resume-002`: `tool_sequence_ok=ok`

So the next implementation target is not "build handoff" or "build compaction" from scratch. The next target is to add model-backed planning safely behind the existing deterministic contract and prove that it improves planner quality without breaking the artifact and eval guarantees.

Implementation gate:

- `projects/coding-agent-v1/docs/model-guided-planner-gate.md`

## Phase 1: Planner Separation

## Objective

Separate the planner from the rest of the loop so that `coding-agent-v1` has a stable planning layer rather than one large embedded heuristic path.

## Why This Comes First

Right now the harness already plans, but the planning logic is tightly tied to the current implementation. If we add long-running behavior and stronger evals before cleaning this boundary, later improvements will be harder to make and harder to test.

## Deliverables

- planner interface or planner service boundary
- preserved rule-based planner backend
- stable task-plan output contract
- stable validation-selection interface
- planner rationale surfaced as structured output

## Concrete Tasks

1. Extract a planner boundary from `agent_loop.py`.
2. Split planning into explicit steps:
   - task classification
   - strategy selection
   - validation selection
   - rationale assembly
3. Preserve the current scored heuristic behavior as the default backend.
4. Move planner-specific evidence and reasons into structured planner outputs rather than implicit loop logic.
5. Add tests that assert parity with the current planner behavior on core task classes.

## Files Likely Touched

- `projects/coding-agent-v1/src/coding_agent_v1/agent_loop.py`
- `projects/coding-agent-v1/src/coding_agent_v1/planner.py`
- `projects/coding-agent-v1/src/coding_agent_v1/models.py`
- `projects/coding-agent-v1/tests/test_agent_loop.py`

## Exit Criteria

- agent loop no longer owns detailed planner rules directly
- current planner behavior still passes existing tests
- planner output is explicit enough to swap backends later

## Phase 2: Long-Run Handoff And Resume

## Objective

Upgrade the current resume behavior into a real continuation layer for interrupted work.

## Why This Comes Second

The harness papers make long-running continuity a core differentiator. The current system resumes, but it does not yet have a strong handoff artifact or a clean fresh-session continuation path.

## Deliverables

- handoff artifact format
- save-handoff behavior on interruption or incomplete completion
- resume-from-handoff behavior
- richer resume summary in session artifacts

## Concrete Tasks

1. Define a handoff artifact schema.
2. Generate handoff artifacts from incomplete or interrupted sessions.
3. Include:
   - original request
   - selected task flow
   - current task plan
   - key inspected files
   - changed files
   - validation state
   - blocker or failure summary
   - next recommended step
4. Add a load path so a new session can resume directly from the handoff artifact.
5. Add tests for:
   - interrupted diagnose flow
   - interrupted fix flow
   - interrupted feature flow

## Files Likely Touched

- `projects/coding-agent-v1/src/coding_agent_v1/session_store.py`
- `projects/coding-agent-v1/src/coding_agent_v1/models.py`
- `projects/coding-agent-v1/src/coding_agent_v1/agent_loop.py`
- `projects/coding-agent-v1/tests/test_session_store.py`
- `projects/coding-agent-v1/tests/test_agent_loop.py`

## Exit Criteria

- incomplete runs emit handoff artifacts
- resumed runs can load handoff state directly
- resume no longer depends only on raw prior session replay

## Phase 3: Context Compaction

## Objective

Add a compaction layer so the harness can reduce growing session state into a smaller working summary while preserving continuation quality.

## Why This Comes Third

Handoff alone helps recovery, but compaction is what turns short resume into actual long-running harness support.

## Deliverables

- compaction policy
- compact working summary artifact or stored summary field
- rules for what must be preserved during compaction
- tests that prove resume quality survives compaction

## Concrete Tasks

1. Define compaction triggers.
2. Decide what summary fields are mandatory:
   - current goal
   - task flow
   - current plan
   - strongest evidence
   - changed files
   - latest validation state
   - blocker
   - next step
3. Implement compaction from session events into a smaller persisted summary.
4. Make resumed runs prefer the compact summary plus handoff artifact over full raw history.
5. Add tests for compaction-preserved continuation.

## Files Likely Touched

- `projects/coding-agent-v1/src/coding_agent_v1/session_store.py`
- `projects/coding-agent-v1/src/coding_agent_v1/agent_loop.py`
- `projects/coding-agent-v1/src/coding_agent_v1/models.py`
- `projects/coding-agent-v1/tests/test_session_store.py`
- `projects/coding-agent-v1/tests/test_agent_loop.py`

## Exit Criteria

- compaction reduces session state to a smaller continuation surface
- resumed behavior remains correct after compaction

## Phase 4: Resume And Validation Eval Expansion

## Objective

Put pressure on the two most important remaining weak spots: long-run continuation and validation selection.

## Why This Comes Fourth

After planner separation and long-run support land, the next job is to prove they work under regression pressure.

## Deliverables

- more resume scenarios
- more validation-selection scenarios
- clearer task-class and failure-mode reporting
- saved evidence for planner and validation misses

## Concrete Tasks

1. Add resume eval scenarios for:
   - diagnose then resume
   - repair then resume
   - feature then resume
2. Add validation-selection scenarios for:
   - direct test-file references
   - module-aware rename fallback
   - nested test paths
   - ambiguity fallback to broader validation
3. Extend result summaries to make planner misses and validation misses visible.
4. Add comparison views by task class and failure mode where needed.

## Files Likely Touched

- `projects/coding-agent-v1/src/coding_agent_v1/eval_harness.py`
- `projects/coding-agent-v1/src/coding_agent_v1/eval_catalog.py`
- `projects/coding-agent-v1/tests/test_eval_harness.py`
- `projects/coding-agent-v1/tests/test_cli.py`
- `evals/coding-agent-v1/`

## Exit Criteria

- resume quality is benchmarked, not assumed
- validation-selection behavior is covered across common and tricky cases
- regressions in these areas are easy to spot

## Phase 5: Artifact Contract And Review Surface

## Objective

Make the harness reviewable without forcing a reviewer to reverse-engineer behavior from implementation details.

## Why This Comes Fifth

Once the main functionality is in place, the final step is to make it legible and inspectable.

## Deliverables

- artifact contract doc
- handoff artifact doc
- review command examples
- examples of how to inspect session, eval, comparison, and baseline artifacts

## Concrete Tasks

1. Document the artifact types and fields.
2. Document how artifacts relate to each other.
3. Add README examples for:
   - running a session
   - resuming from handoff
   - running evals
   - comparing against a baseline
4. Add a reviewer-oriented summary doc describing what to inspect first.

## Files Likely Touched

- `projects/coding-agent-v1/README.md`
- `harness-design/`
- `projects/` docs as needed

## Exit Criteria

- artifact model is documented
- reviewer entry path is clear
- the repo tells a coherent story without code spelunking

## Phase 6: Hardening Pass

## Objective

Run one final stabilization pass across tests, docs, and artifacts before calling the phase complete.

## Deliverables

- green targeted tests
- green full `coding-agent-v1` suite
- updated docs consistent with implementation
- clean milestone summary

## Concrete Tasks

1. Run targeted tests after each phase.
2. Run full `projects/coding-agent-v1/tests` suite before final signoff.
3. Update roadmap docs if implementation reality changed.
4. Write a short milestone summary of what the harness can now do end to end.

## Exit Criteria

- tests pass
- docs match behavior
- milestone can be reviewed cleanly

## Recommended Working Order Inside The Code

If executing this directly in the repo, the best order is:

1. keep `deterministic_heuristic` as the baseline planner strategy
2. keep `model_guided` behind the existing `TaskPlan` contract
3. add harder planner-quality eval scenarios before enabling model-guided planning by default
4. expand resume and validation stress scenarios
5. harden long-run artifact retention where artifact volume becomes noisy
6. regenerate reviewer evidence after each behavior-significant change
7. run focused tests, then the full `coding-agent-v1` suite before launch

## What We Should Not Do In Parallel

Avoid mixing these together in one giant change:

- model-guided planner implementation
- planner-quality eval expansion
- eval expansion
- retention-policy changes
- docs rewrite

Those should land as separate milestone slices so failures are attributable.

## Best Milestone Names

If we want a clean git story, the next milestone stack should look like:

1. `model-guided-planner-gate`
2. `planner-quality-eval-expansion`
3. `long-run-retention-hardening`
4. `validation-and-resume-stress-pack`
5. `repo-launch-review-bundle`

## Final Definition Of Success

This execution plan succeeds when `coding-agent-v1` can:

- plan through a stable planner layer
- persist rich session state
- recover through explicit handoff artifacts
- continue through compacted summaries
- choose validation intentionally
- prove its quality through repeatable evals
- expose enough artifacts and docs for a reviewer to inspect it end to end

At that point, the harness-design track has been implemented to a serious first endpoint, and later work like subagents or self-improving harness loops can build on a stable base.
