# Harness Design Implementation Roadmap

This file turns the research in `harness-design/` into a concrete build plan for a git-tracked coding-agent project.

Primary inputs:

- `harness-design/AgrenHarnessEngineering.pdf`
- `harness-design/HarnessDesign.pdf`
- `harness-design/LilyBlog.pdf`

Related repo context:

- `projects/coding-agent-from-scratch-implementation-map.md`
- `projects/coding-agent-harness-checklist.md`
- `projects/coding-agent-git-launch-plan.md`
- `projects/coding-agent-v1/`

## One-Sentence Goal

Build a coding-agent harness that can take a small real repository task from request to verified patch, recover across long-running sessions, and measure itself on a repeatable eval suite.

## What The Harness Docs Are Really Telling Us

In simple words:

1. The model is not the product; the harness is the product.
2. Durable files, plans, logs, and evals matter more than long prompts.
3. The agent should be forced to validate its work before claiming success.
4. Long-running work needs resumption, compaction, and explicit handoff artifacts.
5. Repeated failures should become harness rules, hooks, or eval scenarios.

## End-To-End Project Target

The right meaty target is not "chat with code" and not "one nice demo".

The target is:

`coding-agent-harness-v0` that can:

- inspect a repo
- classify a task
- write a plan
- choose safe tools
- make a bounded code change
- run the right validation command
- save artifacts and reasoning
- resume after interruption
- score itself on benchmark tasks

That target is large enough to teach the real system shape, but still small enough to build in stages.

## What This Project Should Teach

If we build this properly, it teaches:

- how agent loops actually work in practice
- why filesystem state beats keeping everything in prompt context
- how permissions and hooks turn guidance into enforcement
- how evals change agent work from demoing to engineering
- how long-running agents need session state, handoffs, and recovery
- how to evolve a harness based on real failure evidence

## Recommended Repo Structure

Use one visible implementation lane instead of scattering ideas:

```text
projects/
  coding-agent-v1/
    src/coding_agent_v1/
      agent_loop.py
      planner.py
      tools.py
      permissions.py
      memory.py
      session_store.py
      validation.py
      eval_harness.py
      artifacts.py
    tests/
    evals/
    artifacts/
    README.md

harness-design/
  AgrenHarnessEngineering.pdf
  HarnessDesign.pdf
  LilyBlog.pdf
  implementation-roadmap.md

projects/
  coding-agent-current-status.md
  coding-agent-from-scratch-implementation-map.md
  coding-agent-git-launch-plan.md
```

Notes:

- Keep the main code in one implementation folder.
- Keep eval cases and artifacts close to the harness, not buried elsewhere.
- Keep research docs separate from the executable system.

## Build Phases

## Phase 0: Lock The System Contract

Before adding features, define what the harness owns.

Deliverables:

- task types: `fix`, `feature`, `rename`, `diagnose`, `resume`
- planner output schema
- artifact directory layout
- validation command selection rules
- success and failure result schema

Why this matters:

- Without a system contract, the harness becomes a pile of heuristics.

## Phase 1: Minimum Working Loop

Build the smallest loop that feels like a real coding agent.

Required behaviors:

- read repo context
- inspect relevant files
- classify task type
- generate a short plan
- choose one bounded action
- execute the action
- run validation
- report pass or failure

Implementation surfaces:

- `agent_loop.py`
- `planner.py`
- `tools.py`
- `validation.py`

Success bar:

- can complete simple single-file and small multi-file tasks with a saved plan and explicit validation result

## Phase 2: Safety And Enforcement

Move from "suggested behavior" to "enforced behavior".

Required behaviors:

- reject destructive commands
- bound command duration and output size
- restrict writes to workspace scope
- require validation before final success
- save tool events and failure reasons

Implementation surfaces:

- `permissions.py`
- `tools.py`
- `artifacts.py`

Success bar:

- invalid or risky actions fail safely and loudly

## Phase 3: Durable Memory And Resumption

This is where the harness starts to feel real instead of toy.

Required behaviors:

- save plan, action history, validation results, and outcome summary
- support interrupted runs
- reload session state
- continue from prior plan and artifacts

Implementation surfaces:

- `memory.py`
- `session_store.py`
- `artifacts.py`

Success bar:

- interrupted work can resume without redoing the entire diagnosis

## Phase 4: Eval Harness

This is the phase that makes the project reviewable.

Required behaviors:

- fixed benchmark task definitions
- repeatable repo setup per task
- pass/fail scoring
- saved run artifacts
- regression comparison against previous baseline

Implementation surfaces:

- `eval_harness.py`
- `evals/`
- test coverage for eval flows

Success bar:

- we can run a suite and show what improved, what regressed, and why

## Phase 5: Long-Running Workflow Support

This phase implements the strongest lesson from the harness-design papers.

Required behaviors:

- context compaction or summary artifacts
- explicit handoff file for continuation
- fresh-session continuation
- retained evidence without replaying full logs

Implementation surfaces:

- `memory.py`
- `session_store.py`
- `agent_loop.py`

Success bar:

- the harness can span more than one working session cleanly

## Phase 6: Delegation And Parallelism

Only do this after the single-agent loop is stable.

Required behaviors:

- bounded subagent tasks
- isolated output artifacts
- clear parent-child merge rules
- no overlapping writes without coordination

Implementation surfaces:

- subagent orchestration modules
- artifact merge logic
- delegation tests

Success bar:

- parallelism reduces time or improves search, instead of creating chaos

## First Git-Trackable Milestone

The first strong repo milestone should be:

`coding-agent-harness-v0`

It should prove:

- the harness can complete real small tasks
- every run writes artifacts
- validation is mandatory
- the task loop is testable
- the eval suite is repeatable

This is better than jumping straight to subagents or autonomous long-horizon work.

## Definition Of Done For V0

V0 is done when all of these are true:

- task classification exists and is tested
- planner writes a structured plan with reasons
- code-edit and shell tools are bounded
- validation command selection is deterministic enough to test
- run artifacts include plan, actions, validation, and summary
- resume flow exists for interrupted tasks
- eval suite covers at least 5 meaningful task scenarios
- regression comparison exists for eval runs

## First 10 Issues To Open

These should become actual git issues or tracked tasks.

1. Define the task model and planner output schema.
2. Implement repo inspection and workspace summary generation.
3. Build a bounded shell tool wrapper with output clipping and time limits.
4. Implement file-edit actions with artifact logging.
5. Add validation command selection for `fix`, `rename`, and `feature` flows.
6. Add permission rules for destructive command blocking and workspace path checks.
7. Implement session artifact storage for plans, tool calls, validation, and outcome summaries.
8. Add interrupted-run resumption from saved session state.
9. Build the first eval pack with at least 5 scenarios and saved artifact output.
10. Add regression comparison so new harness changes are judged against a baseline.

## Starter Eval Portfolio

The first eval pack should include a small but varied set of tasks:

1. Single-file bug fix with one obvious failing test.
2. Cross-file rename where the target test does not mention the old symbol directly.
3. Small feature addition with one new behavior and one regression check.
4. Diagnose-only task where the harness should inspect and explain without editing.
5. Resume task where the first run is interrupted and the second run finishes from artifacts.

Why these five:

- they test planning
- they test validation choice
- they test artifact quality
- they test recovery
- they cover more than one happy path

## What Not To Build First

Avoid spending early cycles on:

- fancy prompt experiments without evals
- many-agent orchestration before single-agent stability
- benchmark chasing without artifact review
- custom memory abstractions before plain file-based state works
- broad tool catalogs before a small reliable tool set is stable

## Review Standard For Future Harness Changes

Every harness change should answer four questions:

1. What repeated failure or missing capability does this address?
2. Which harness component is being changed?
3. How will we test that the change helped?
4. What regression risk does it introduce?

If a change cannot answer those questions, it is probably not a good next step.

## Best Big-Picture Sequence

The cleanest story for this repo is:

1. harness research review
2. implementation map
3. working single-agent loop
4. enforced validation and safety
5. durable artifacts and resume
6. eval discipline
7. long-running support
8. subagents only after the core loop is reliable

## Bottom Line

The main lesson from the harness-design material is not "use a smarter model."

It is:

build a system where the agent can plan, act, validate, remember, recover, and be measured.

That is the implementation standard this repo should aim for.
