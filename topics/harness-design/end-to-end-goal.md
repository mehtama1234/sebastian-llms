# End-To-End Goal: Build A Behavior-Aware Coding Agent Harness

## One-Sentence Goal

Build `projects/coding-agent-v1` into a small but serious coding-agent harness that can take a real repo-change request, identify the behavior being changed, plan against the right source surfaces, execute a bounded code edit, preserve useful working state, resume after interruption, learn from repeated failure patterns through reviewable repair records, and prove the result through repeatable evals.

## Meaty End-To-End Implementation Goal

Build a local coding-agent harness that proves a full engineering loop, not just a single agent response.

The flagship goal is:

```text
Given a real change request against coding-agent-v1, the harness can plan the work by affected behavior, execute or block safely, preserve the useful state of the run, resume from that state, convert meaningful failures into reviewable repair memory, and prove through evals and baseline comparison that the harness behavior improved without regressions.
```

In simple words, we are building the operating system around a coding agent:

- the behavior map that tells the agent what part of itself a task touches
- the planner contract that says why these files, tests, and actions are relevant
- the working memory that separates Belief, Progress, and Experience
- the compact context that lets a long run continue without replaying every log line
- the handoff artifact that lets a blocked run be resumed by a later run
- the procedural repair memory that turns repeated failures into reusable lessons
- the eval harness that checks behavior, tool sequence, escalation, traces, and regressions

The end-to-end demo should answer one hard reviewer question:

```text
Can this harness make a coding agent's work inspectable, restartable, repairable, and measurable?
```

The expected proof path is:

1. Start with a task such as `improve validation selection for rename or resume tasks`.
2. Produce a `TaskPlan` with planner strategy, task flow, affected behavior IDs, implementation surfaces, validation command, and rationale.
3. Persist a session with request, events, result, touched files, and BPE memory.
4. Save a compact continuation artifact with the state needed to resume.
5. Force or simulate a blocked run that writes a handoff artifact.
6. Resume from the handoff and show the previous BPE state was carried forward.
7. Create a candidate procedural repair record from the failure boundary.
8. Recall that repair record in a later similar run as Experience.
9. Run the core eval pack and trace-oriented smoke eval pack.
10. Compare candidate results against a named baseline and report regressions, expectation regressions, and task-class deltas.

This is done only when a reviewer can inspect the saved artifacts and see the entire chain:

```text
request -> behavior plan -> execution state -> compact context -> handoff -> resume -> repair memory -> eval traces -> baseline comparison
```

That is the project. Not a generic chatbot. Not a one-off demo. A reviewable harness for improving coding agents.

## Plain-English Version

We are not trying to build a giant autonomous software engineer.

We are building the harness around a coding agent.

The harness should make the agent more reliable by answering five practical questions during every run:

1. What behavior is this task trying to change?
2. Where does that behavior live in the code?
3. What does the agent currently believe, what has it already done, and what prior experience should it reuse?
4. If the run fails or gets interrupted, what exact artifact lets another run continue?
5. Did the latest harness change actually improve eval results, or did it regress something?

That is the end-to-end point: a coding-agent harness that is inspectable, resumable, measurable, and safe enough to improve incrementally.

## Why This Is The Right Goal

The reviewed harness-design papers point to the same implementation lesson:

- `Harness Handbook`: agents need a behavior-to-code map, because requested behavior rarely maps cleanly to one filename or keyword.
- `Living-Harness`: failed episodes should become persistent procedural repair knowledge, not just one-off logs.
- `EvoHarness-RL`: long-running agents need structured runtime memory, especially Belief, Progress, and Experience.

For this project, the practical translation is:

- behavior must be locatable
- planning must cite behavior evidence
- working memory must be structured
- handoff/resume must be first-class
- failures must create reusable repair records
- evals must measure these behaviors directly

## Flagship Demo

The main demo should be a harness-improvement task against `coding-agent-v1` itself.

Example task:

```text
Improve validation selection so rename tasks choose the right targeted test even when the old symbol is not mentioned in the test file.
```

The completed demo should show this full loop:

1. The behavior index identifies `validation_selection` as the affected behavior.
2. The planner maps the request to the relevant implementation surfaces, such as planner, agent loop, eval harness, and tests.
3. The harness executes a bounded edit against the repo.
4. The session records Belief, Progress, and Experience.
5. The selected validation command has an explicit reason.
6. If the run fails, a handoff artifact captures the blocker and next step.
7. A resumed run can continue from that handoff without replaying the whole history.
8. A procedural repair record captures the failure pattern and recommended recovery.
9. An eval scenario proves the behavior.
10. A baseline comparison shows whether this was an improvement or a regression.

If that demo works, the harness thesis is proven in one concrete loop.

## End-To-End Implementation Target

The implementation target is a complete local proof loop, not a slide deck or a passive design document.

Given a real request like:

```text
Improve validation selection for coding-agent-v1.
```

the harness should produce the following chain of evidence:

1. A `TaskPlan` that names the planner strategy, task flow, affected behavior IDs, implementation surfaces, validation command, and rationale.
2. A persisted session record that stores the request, plan, events, validation result, touched files, and BPE working memory.
3. A compact continuation artifact that preserves the useful state needed to resume without replaying raw logs.
4. A handoff artifact when the run is blocked by permission, approval, or validation failure.
5. A resumed session that carries forward the prior Belief, Progress, and Experience state.
6. A procedural repair record when a failure pattern is important enough to reuse.
7. A later run that recalls the repair record into Experience instead of rediscovering the same lesson from scratch.
8. Eval results and trace artifacts that expose behavior IDs, BPE presence, compact-context use, repair IDs, tool sequence, and escalation behavior.
9. A baseline comparison artifact that shows regressions, expectation regressions, task-class deltas, and behavior-level impact.
10. A reviewer package that lets another engineer inspect all of this from files and commands.

That is the practical implementation definition of "coding agent stuff" for this project: build the machinery that makes an agent run explainable, restartable, debuggable, and measurable.

## What The System Must Teach

This project should teach the difference between a simple tool-calling loop and a real coding-agent harness.

Specifically, it should teach:

1. How to turn a vague coding request into a behavior-level plan.
2. How to map behavior to implementation files and tests.
3. How to preserve long-running context without keeping endless raw logs.
4. How to make interruption and continuation explicit instead of accidental.
5. How to convert failures into procedural memory without allowing unsafe self-modification.
6. How to use evals as pressure on harness behavior, not just final code correctness.
7. How to inspect whether an agent made a good decision after the run is over.

## Required Capabilities

### 1. Behavior Index

The harness needs a behavior-centered map of itself.

Initial behavior IDs:

- `task_classification`
- `task_planning`
- `validation_selection`
- `permission_decisions`
- `tool_execution`
- `session_persistence`
- `handoff_and_resume`
- `eval_execution`
- `eval_comparison`
- `baseline_promotion`
- `failure_memory`

Each behavior entry should include:

- behavior id
- short description
- relevant source files
- relevant functions/classes
- related state
- related tests
- verification status

Acceptance test:

- Given a task about validation selection, the harness returns `validation_selection` and points to the relevant implementation and tests.

### 2. Behavior-Guided Planning

The planner must use the behavior index when building a task plan.

The task plan should include:

- task flow
- planner strategy
- affected behavior IDs
- implementation surfaces
- validation command
- rationale

Acceptance test:

- A resume-related request points to `handoff_and_resume` and `session_persistence`.
- A validation-related request points to `validation_selection`.
- A failure-memory request points to `failure_memory`.

### 3. BPE Working Memory

Working memory must be split into:

- Belief: facts the harness currently believes about the repo, task, files, failures, and assumptions.
- Progress: what has been done, what changed, what validation ran, what remains, and what is blocked.
- Experience: prior similar sessions, recalled repair records, known failure patterns, and successful recovery recipes.

Acceptance test:

- Every persisted session record contains non-empty BPE fields for a meaningful run.
- A reviewer can understand the run without reading raw terminal logs.

### 4. Handoff And Resume

Incomplete or blocked runs must create a handoff artifact.

The handoff artifact should include:

- original request
- task flow
- affected behavior IDs
- Belief state
- Progress state
- Experience state
- touched files
- validation state
- blocker
- next recommended action

Acceptance test:

- A run that hits a permission boundary, approval boundary, or validation failure writes a handoff.
- A later run can resume from that handoff and carry forward the useful BPE state.

### 5. Context Compaction

The harness must compact long session history into BPE-shaped continuation state.

Compaction should preserve:

- active goal
- affected behavior IDs
- current plan
- important evidence
- touched files
- latest validation status
- unresolved blocker
- next step
- relevant prior experience

Compaction should discard:

- redundant command output
- stale intermediate observations
- repeated log noise
- raw details already captured in artifacts

Acceptance test:

- A resumed run can use compacted BPE state instead of full raw history and still select the right next action.

### 6. Procedural Repair Memory

The harness must turn repeated or important failures into structured repair records.

A repair record should include:

- repair id
- source session id
- task class
- trigger condition
- failure pattern
- recommended recovery
- source evidence
- validation evidence
- affected behavior IDs
- support count
- status

Allowed statuses:

- `candidate`
- `accepted`
- `rejected`
- `retired`

This phase should keep repairs reviewable and bounded. The harness can recommend or recall a repair, but it should not freely rewrite its own rules without a human or policy gate.

Acceptance test:

- A validation-selection failure creates a candidate repair record.
- A later similar task recalls that repair record and includes it in Experience.

### 7. Eval Pressure

The eval system must measure the new harness behaviors directly.

Required eval categories:

- behavior localization
- planner behavior selection
- validation selection
- BPE memory persistence
- handoff fidelity
- resume from handoff
- procedural repair creation
- procedural repair reuse
- regression comparison by task class and behavior id

Each eval result should expose:

- pass/fail
- reason
- task class
- affected behavior IDs
- repair record IDs, if any
- whether BPE memory was present
- failure mode
- baseline comparison result

Acceptance test:

- Eval output lets us answer: did this harness change improve or regress `validation_selection`, `handoff_and_resume`, or `failure_memory`?

## Implementation Milestones

### Milestone 1: Behavior-Aware Planning

Deliver:

- behavior index module
- behavior IDs on task plans
- implementation surfaces on task plans
- planner tests for behavior selection

Done when:

- plans are no longer just task-class guesses; they cite behavior evidence.

### Milestone 2: BPE Session State

Deliver:

- BPE fields in working memory
- persisted BPE session artifacts
- review summaries that show BPE state

Done when:

- a run can be inspected through Belief, Progress, and Experience instead of raw logs.

### Milestone 3: Handoff And Resume

Deliver:

- handoff artifact model
- save-handoff on blocked/incomplete runs
- resume-from-handoff command
- tests for permission, approval, and validation-failure handoffs

Done when:

- a new process can continue from a prior blocked run with useful state intact.

### Milestone 4: Procedural Repair Memory

Deliver:

- repair record model
- repair creation from failures
- repair retrieval by task class and behavior id
- CLI review commands

Done when:

- recurring failures become reviewable candidate repairs and are recalled in later runs.

### Milestone 5: Eval And Baseline Proof

Deliver:

- behavior IDs in eval results
- repair IDs in eval results
- BPE presence in eval results
- trace artifacts with harness state
- baseline comparison by task class and behavior id

Done when:

- the harness can prove the flagship demo improved the targeted behavior without silently regressing another core behavior.

### Milestone 6: Reviewer Package

Deliver:

- documented artifact contracts
- example commands
- example session artifacts
- example eval summary
- final milestone note explaining what was built and what remains

Done when:

- another engineer can review the harness from docs, commands, artifacts, and tests without needing a verbal explanation.

## Definition Of Done

This goal is done when `coding-agent-v1` can run the flagship demo end to end and produce reviewable evidence for:

- behavior localization
- behavior-guided planning
- BPE working memory
- bounded execution
- targeted validation
- handoff and resume
- procedural repair capture
- procedural repair recall
- eval proof
- baseline comparison

The bar is not "the agent edited a file."

The bar is "the harness can explain, persist, resume, learn from, and evaluate the coding-agent run."

For completion, the evidence must include:

- passing focused harness tests
- a saved demo session bundle
- at least one compact resume path
- at least one handoff and handoff-resume path
- at least one procedural repair record and a recall path
- at least one eval pack run with trace artifacts
- at least one baseline comparison showing whether the candidate regressed
- docs that point to the exact commands and artifacts a reviewer should inspect

## Reviewer Package

The current reviewer package for proving this goal lives in:

- `projects/coding-agent-v1/docs/artifact-contract.md`
- `projects/coding-agent-v1/docs/flagship-demo-runbook.md`
- `projects/coding-agent-v1/docs/flagship-demo-evidence-20260809.md`
- `projects/coding-agent-v1/docs/milestone-summary.md`

Use the artifact contract to inspect saved session, compaction, handoff, repair, eval, trace, baseline, and decision artifacts.

Use the flagship runbook to execute the end-to-end proof path.

## Non-Goals For This Phase

This phase does not include:

- autonomous self-editing without review
- reinforcement learning
- multi-agent orchestration
- cloud deployment
- arbitrary large-repo support
- production-grade sandboxing beyond the current local harness boundary

Those can come later. This phase builds the substrate that would make those future steps credible.

## Short Version

Build `coding-agent-v1` into a behavior-aware, resumable, measurable coding-agent harness. It should know what behavior a task affects, where that behavior lives in code, what state must survive across sessions, what failures should become reusable repair knowledge, and whether each harness change improves or regresses eval performance.
