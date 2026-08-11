# LLM Developments 2026 Implementation Roadmap

## Phase 0: canonical framing

Deliverables:

- implementation review note
- project track README
- detailed implementation targets
- eval lane README and benchmark plan

Question answered:

which papers from `LLMDevelopments.pdf` actually deserve implementation time?

## Phase 1: retrieval and context systems

Build:

- lexical retrieval adapter
- vector retrieval adapter
- hybrid retrieval adapter
- inline tool-output injection mode
- file-pointer tool-output mode
- token and latency accounting for retrieval payloads

Exit criteria:

- one repeatable retrieval benchmark exists
- cost, latency, and task-success tradeoffs are measurable

## Phase 2: repo-context loading experiments

Build:

- no-context baseline
- single-root context-file mode
- hierarchical context-file mode
- selective context-file loading rules

Exit criteria:

- context-file usefulness is measured by task class
- instruction bloat versus task benefit is explicit

## Phase 3: reasoning and verifier systems

Build:

- multi-candidate planning mode
- verifier scoring for plans and outputs
- stop-on-confidence policy
- shared-evidence branch mode for parallel planning

Exit criteria:

- `k`-attempt scaling curves exist for at least one task family
- verifier loops reduce ungrounded outputs or bad edits

## Phase 4: harness schema and workflow presets

Build:

- typed harness configuration
- trace schema
- task-class-specific harness presets
- comparable run manifests

Exit criteria:

- harness variants are first-class comparable artifacts
- task presets can be benchmarked against generic behavior

## Phase 5: long-horizon CLI eval pack

Build:

- multi-step inspect tasks
- diagnose-only tasks
- bug-fix tasks
- feature tasks
- rename and refactor tasks
- resume-after-interruption tasks

Exit criteria:

- at least one local benchmark pack exists for terminal-first software-engineering agents
- failures are labeled by stage, not only by final outcome

## Phase 6: asynchronous execution and handoff

Build:

- checkpointed task artifacts
- resumable background task flow
- explicit handoff bundle for long-running jobs

Exit criteria:

- at least one long-running repo task can pause and resume safely
- the repo has a durable handoff format for extended work

## Phase 7: long-context systems prototypes

Build:

- cache-eviction simulator
- compressed-history memory simulator
- local-window plus compressed-history comparison
- sparse-index reuse prototype

Exit criteria:

- long-context tradeoffs are measurable without full frontier-scale training
- at least one architecture-lane prototype is strong enough to promote into deeper testing

## Phase 8: reduced architecture promotion pass

Build:

- one concept-selection memo for architecture-worthy ideas
- one promotion path into `code/architecture-advances-2026/`
- one benchmark plan for each promoted concept

Exit criteria:

- at least one long-context or sparse-access concept graduates into the architecture sandbox

## Phase 9: default-harness promotion pass

Build:

- one recommendation memo for retrieval defaults
- one recommendation memo for context-file loading defaults
- one recommendation memo for verifier usage
- one recommendation memo for asynchronous execution defaults

Exit criteria:

- `projects/coding-agent-v1/` has a clear adoption plan
- the repo knows which ideas from this paper set are real production candidates
