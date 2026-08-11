# Deep Review: Self-Evolving Harness Papers

Reviewed papers:

- `2607.13285v1.pdf`: Harness Handbook: Making Evolving Agent Harnesses Readable, Navigable, and Editable
- `2607.26598v1.pdf`: Living-Harness Is an Interactive-Agent Evolver
- `2608.05446v1.pdf`: EvoHarness-RL: Learning Self-Evolving Runtime Harness for Long-Horizon LLM Agents

Reviewed on: August 9, 2026

## Executive Takeaway

These three papers push the harness-design track beyond "agent loop plus tools".

Together, they say a serious coding-agent harness needs three deeper layers:

1. A behavior map that links requested behavior to source code.
2. A procedural memory layer that turns repeated failures into reusable repairs.
3. A runtime state interface that separates what the agent believes, what progress it has made, and what experience it can reuse.

For our `coding-agent-v1`, the practical lesson is:

Do not jump straight to autonomous self-improvement. First implement the missing substrate:

- behavior-indexed repository understanding
- explicit handoff and progress state
- failure-pattern memory
- validation and planner miss tracking
- eval-driven update proposals

That gives us the engineering foundation for future self-evolving harness work without building an unsafe or unreviewable auto-editing loop too early.

## Paper 1: Harness Handbook

File:

- `harness-design/2607.13285v1.pdf`

Core idea:

- Harness evolution is blocked by behavior localization.
- A request says what behavior should change, but the repo is organized by files, functions, and modules.
- The missing layer is a behavior-centered map from system behavior to implementation sites.

The paper proposes:

- Harness Handbook: a behavior-centric representation of a harness codebase
- Behavior-Guided Progressive Disclosure: a navigation workflow from high-level behavior to specific code locations
- automatic synchronization between handbook entries and current source locations

The handbook has three levels:

- L1: system overview
- L2: component or stage overview
- L3: source-backed unit details

It also keeps a state-register view for cross-stage state relationships.

Why this matters:

- Coding agents often fail before editing because they edit the wrong place or miss one of several related locations.
- Search and repo maps help, but they remain code-centric.
- A behavior map makes the agent start from "what behavior am I changing?" instead of "what keyword should I grep?"

Evaluation claim:

- Tested on Codex and Terminus-2 harness modification requests.
- Handbook-assisted planning improved plan quality and reduced token use.
- Reported overall win-rate gains were 10.0 percentage points on Codex and 18.9 percentage points on Terminus-2.
- Planner token use dropped by 12.7% for Codex and 8.6% for Terminus-2.
- The biggest gains came from cross-file and search-hostile requests.

Most important implementation lesson for us:

- Add a behavior index before trying to add smarter planning.

For `coding-agent-v1`, this means we should create a lightweight version of Harness Handbook:

- list the harness behaviors
- map each behavior to modules/functions
- expose this map to planner selection
- keep the source anchors revalidated

Example behavior entries:

- task classification
- validation command selection
- permission gating
- session persistence
- eval comparison
- baseline promotion
- resume flow

This should become a concrete implementation surface, not just documentation.

## Paper 2: Living-Harness

File:

- `harness-design/2607.26598v1.pdf`

Core idea:

- Agents may recover inside one episode, but the same failure can recur later because the correction does not update the persistent harness.
- A harness should turn evaluated failures into persistent procedural repairs.

The paper proposes:

- Living-Harness: a rollout, evaluate, update loop
- fixed tools and base context
- evolving episodic memory
- evolving state graph
- domain-level Evolution-SOP that governs bounded updates

The important separation:

- frozen: tools and base context
- evolving: memory and workflow state

This matters because it keeps adaptation bounded. The system learns from failures, but it does not freely rewrite its operational boundary.

The two persistent stores are:

- episodic memory: trigger conditions, failure patterns, recovery actions
- state graph: state nodes, repair edges, transition rules

Evaluation claim:

- Tested on interactive task benchmarks derived from tau2-Bench and MultiWOZ-2.4.
- Reported average Pass@1 improved to 83.09 on tau2-Bench and 65.50 on MultiWOZ-2.4.
- The paper reports around 10 point gains over strongest interactive baselines.
- Ablations show the Evolution-SOP caused the largest drop when removed, with memory and state graph also contributing.
- The evolved harness state transferred across model backbones through retrieval-only reuse.

Most important implementation lesson for us:

- Do not merely save session logs.
- Convert repeated failures into structured repair records that future runs can retrieve.

For `coding-agent-v1`, this suggests adding a `FailureMemory` or `ProceduralRepair` layer:

- trigger: when this issue appears
- failure pattern: what went wrong
- recovery action: what should be tried next
- affected task class
- validation evidence
- source locations
- confidence or support count

Example repair records:

- "For rename tasks where tests import the module but do not mention the old symbol, use module-aware validation fallback."
- "For passive failure reports, diagnose before editing."
- "For ambiguous feature requests, prefer inspection plus plan over direct edit."

This is directly aligned with our current roadmap around planner misses and validation misses.

## Paper 3: EvoHarness-RL

File:

- `harness-design/2608.05446v1.pdf`

Core idea:

- Long-horizon agents need external state, but they also need to learn when to use that state.
- The harness should expose a compact runtime state interface, and the agent should coordinate with it through a small action protocol.

The paper proposes:

- EvoHarness-RL
- BPE state abstraction: Belief, Progress, Experience
- compact harness actions: track, commit, recall, note
- supervised training to teach harness actions
- GRPO to optimize when harness access is worth the cost

The BPE split is the most useful part for our implementation.

Belief:

- what the agent currently thinks is true about the repo, tests, failures, and files

Progress:

- what has been done, what is pending, and where the task is blocked

Experience:

- reusable lessons from prior tasks, failures, evals, and repairs

Evaluation claim:

- Tested on ALFWorld with Qwen3-8B.
- Prompt-time BPE improved frozen inference behavior.
- SFT improved harness-call use.
- GRPO reached 96.9% success on seen tasks and 86.6% on unseen tasks.
- Ablations showed that removing Belief, Progress, or Experience hurt performance.

Most important implementation lesson for us:

- Structure our runtime memory as Belief, Progress, and Experience before worrying about RL.

For `coding-agent-v1`, this maps cleanly:

- Belief: workspace summary, discovered files, current failure evidence, inferred task facts
- Progress: task plan, completed actions, changed files, validation status, next step
- Experience: prior failure patterns, planner misses, validation misses, successful repair recipes

The compact action protocol also maps cleanly:

- track: inspect repo or focused source/test state
- commit: persist plan/progress/validation state
- recall: retrieve relevant prior repairs or behavior-map entries
- note: write a new insight from the current run

We do not need RL now. But we should design the state and actions so the harness could become trainable or optimizable later.

## Combined Architecture Lesson

The three papers fit together like this:

1. Harness Handbook tells us how to find where behavior lives in code.
2. Living-Harness tells us how to turn evaluated failures into persistent procedural repairs.
3. EvoHarness-RL tells us how to structure runtime state so the agent can use it during long-horizon work.

Together, they imply this architecture:

```text
User Request
  -> Task Classifier
  -> Behavior Index / Harness Handbook
  -> Planner
  -> BPE Runtime State
       Belief: repo and failure facts
       Progress: plan and execution status
       Experience: prior repairs and lessons
  -> Tool Runtime
  -> Validation
  -> Artifact Store
  -> Failure / Success Analysis
  -> Procedural Repair Proposal
  -> Human-reviewed or policy-gated update
```

That is the right north star for our remaining implementation.

## How This Changes Our Roadmap

The prior execution plan was directionally right:

- planner separation
- handoff and resume
- compaction
- eval expansion
- artifact contracts

These papers make three additions important.

## Addition 1: Behavior Index Before Model Planner

Before adding a model-backed planner, add a behavior-index layer.

Reason:

- The Handbook paper shows the planner performs better when it navigates by behavior first.

Implementation:

- create a behavior map for `coding-agent-v1`
- map behavior names to source modules and functions
- use the behavior map during planning and review
- revalidate anchors against the current source

## Addition 2: Failure Memory Before Self-Editing

Before allowing the harness to evolve itself, add structured failure memory.

Reason:

- Living-Harness shows the value comes from bounded procedural repair, not raw logs.

Implementation:

- define failure records
- capture planner misses and validation misses
- store repair suggestions
- retrieve relevant repairs in later plans
- keep actual harness edits human-reviewed for now

## Addition 3: BPE Memory Model For Resume

Before building deep context compaction, organize memory into Belief, Progress, and Experience.

Reason:

- EvoHarness-RL shows that long-horizon state works better when the external state has clear functional roles.

Implementation:

- update working memory to expose belief/progress/experience fields
- make handoff artifacts use the same structure
- make compaction preserve these fields

## Recommended Updated Build Order

The new best order is:

1. implement behavior index for `coding-agent-v1`
2. refactor planner to consume behavior-index evidence
3. introduce BPE-shaped working memory
4. add explicit handoff artifacts using BPE fields
5. add context compaction over BPE fields
6. add failure memory for planner and validation misses
7. expand evals to cover behavior localization, resume, and validation selection
8. document artifact contracts and review commands

This is a better order than planner-only refactoring because the planner needs better behavioral evidence, not just cleaner interfaces.

## Specific Implementation Implications

## 1. Add `behavior_index.py`

Purpose:

- maintain behavior-to-code mappings for the harness itself

Initial entries:

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

Each entry should include:

- behavior id
- description
- source files
- important functions or classes
- related state
- validation tests
- last verified status

## 2. Add Planner Evidence From The Behavior Index

Purpose:

- make task planning behavior-aware

The planner should be able to say:

- this request affects `validation_selection`
- likely source files are `agent_loop.py`, `planner.py`, and `test_agent_loop.py`
- related eval surface is `eval_harness.py`

This directly implements the Harness Handbook lesson at small scale.

## 3. Reshape Working Memory Into BPE

Purpose:

- make long-running state easier to reason about

Suggested shape:

```text
belief:
  repo facts
  relevant files
  current failure evidence
  inferred task facts

progress:
  task plan
  completed actions
  changed files
  validation state
  blocker
  next step

experience:
  recalled repair records
  prior similar tasks
  planner warnings
  validation warnings
```

## 4. Add Procedural Repair Records

Purpose:

- turn recurring misses into reusable harness knowledge

Suggested fields:

```text
repair_id
task_class
trigger_condition
failure_pattern
recommended_recovery
source_evidence
validation_evidence
support_count
status
```

Status values:

- `candidate`
- `accepted`
- `rejected`
- `retired`

For now, acceptance should be human-reviewed or test-gated. Do not let the harness freely edit its own rules.

## 5. Expand Evals Around The New Ideas

New eval categories:

- behavior localization: can the planner identify the right harness component?
- planner miss memory: does a known prior miss improve later planning?
- validation miss memory: does the harness avoid repeating bad validation choices?
- BPE resume: can a resumed run continue from structured belief/progress/experience?
- handoff fidelity: does the handoff preserve enough state for a fresh session?

## What To Avoid

Avoid these mistakes:

- building autonomous self-editing before failure memory and evals are stable
- treating all prior runs as raw context instead of structured experience
- adding a model planner before giving it behavior-level navigation
- making the behavior index a stale doc with no source-anchor checks
- optimizing for benchmark scores before artifact review is clear

## Best Near-Term Milestone

The next strong milestone should be:

`behavior-index-and-bpe-memory`

It should deliver:

- behavior index for the harness
- planner use of behavior-index evidence
- BPE-shaped working memory
- handoff artifact using BPE fields
- tests for behavior localization and BPE resume

That milestone directly combines all three papers while staying implementable in the current repo.

## Bottom Line

These papers do not say "make the agent more autonomous immediately."

They say:

- make behavior easier to locate
- make state easier to reuse
- make failures become structured repair knowledge
- make runtime memory explicit enough to support long-horizon work

For `coding-agent-v1`, the right next implementation move is a behavior index plus BPE memory and handoff support. That is the practical bridge from the current harness to a serious self-evolving harness later.
