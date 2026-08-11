# Detailed Implementation Targets

This document defines the full implementation target set for `LLMDevelopments.pdf`.

The goal is to use the whole paper map, not just the coding-agent subsection.

## Program Objective

Build a production-oriented LLM systems lab inside this repo that can:

- prototype model- and harness-level ideas from 2026 papers
- run repeatable experiments against those ideas
- promote only the ideas that survive measurement
- feed the winning ideas into real agent and long-context systems in this repo

The final output is not one model and not one benchmark.

The final output is a reusable experimentation stack with clear adoption decisions.

## Target Set A: Retrieval and Context Systems

### Target A1: retrieval adapter layer

Implement:

- lexical retrieval
- vector retrieval
- hybrid retrieval
- configurable chunking policy
- configurable reranking policy
- retrieval result accounting

Production questions answered:

- when is lexical search enough?
- when does vector retrieval justify its overhead?
- when should hybrid retrieval become default?

Success criteria:

- the same task can run under all three retrieval modes
- cost, latency, and success metrics are captured consistently

### Target A2: context assembly and pressure control

Implement:

- inline tool-result injection
- file-pointer result delivery
- selective file inclusion
- context budget accounting
- context compaction and summarization rules

Production questions answered:

- when should results stay inline?
- when should the harness hand back a pointer instead?
- how much context expansion is actually worth paying for?

Success criteria:

- each run reports prompt growth and context-source composition
- context policy can be varied independently from retrieval mode

### Target A3: repo instruction loading

Implement:

- no-context baseline
- root instruction file mode
- hierarchical instruction files
- conditional instruction loading by task type and repo area

Production questions answered:

- do repo instructions help or just create token and exploration drag?
- should instructions live at the root, near subtrees, or both?

Success criteria:

- instruction-loading behavior is explicit in traces
- task quality and cost tradeoffs are measurable

## Target Set B: Reasoning and Test-Time Compute

### Target B1: multi-attempt planning

Implement:

- one-shot baseline
- multi-candidate planning
- shared-evidence branch planning
- candidate ranking before execution

Production questions answered:

- when is one attempt enough?
- when do multiple reasoning branches improve outcome quality?

Success criteria:

- task runs can vary candidate count without changing other settings
- gains and runtime cost are visible in evaluation output

### Target B2: verifier layer

Implement:

- answer-grounding checks
- tool-result grounding checks
- test-result consistency checks
- patch-risk checks
- final-output confidence scoring

Production questions answered:

- which failures are preventable with cheap verification?
- when should the system stop, retry, or escalate?

Success criteria:

- verifier outcomes are logged separately from task outcomes
- verifier lift is measurable against a baseline

### Target B3: stop-and-escalate policy

Implement:

- stop-on-confidence thresholds
- retry-on-uncertainty thresholds
- escalate-on-risk thresholds
- capped attempt budgets

Production questions answered:

- when should the agent keep thinking?
- when should it hand off rather than bluff or over-edit?

Success criteria:

- every stop, retry, and escalate action has an explicit recorded reason

## Target Set C: Agent Harness and Workflow Systems

### Target C1: harness schema

Implement:

- typed harness configuration
- serializable run configuration
- trace schema for retrieval, tool use, planning, execution, and verification

Production questions answered:

- which harness changes actually caused quality shifts?
- can runs be compared without informal guesswork?

Success criteria:

- harness variants are first-class artifacts in the repo

### Target C2: task-class-specific harness presets

Implement presets for:

- inspect
- diagnose
- bug fix
- feature work
- rename/refactor
- research and synthesis

Production questions answered:

- should one generic harness handle everything?
- where do specialized presets outperform one-size-fits-all behavior?

Success criteria:

- presets can be selected explicitly or by task router
- preset-level comparisons exist in eval results

### Target C3: asynchronous execution and handoff

Implement:

- checkpoint artifacts
- resumable job state
- paused-task summaries
- long-running task handoff bundle

Production questions answered:

- how should multi-hour tasks pause and resume safely?
- what artifact contract is required for another process or operator to continue?

Success criteria:

- at least one long-running task can be paused, resumed, and handed off without context loss

## Target Set D: Long-Horizon CLI and Agent Evaluation

### Target D1: CLI benchmark pack

Implement benchmark scenarios for:

- inspect and summarize
- diagnose without editing
- targeted bug fix
- bounded feature implementation
- safe rename
- interrupted resume
- long-context retrieval

Production questions answered:

- what does “good” look like for a terminal-first agent in this repo?
- which task families fail for which reasons?

Success criteria:

- benchmark scenarios have expected outcomes and failure labels
- benchmark runs produce comparable machine-readable artifacts

### Target D2: stage-level evaluation

Implement grading for:

- retrieval choice
- context assembly quality
- tool-choice quality
- argument quality
- execution success
- verification correctness
- final-answer grounding

Production questions answered:

- where exactly did a run fail?
- what class of fix should be attempted next?

Success criteria:

- failed tasks can be decomposed into stage failures rather than a binary pass/fail

### Target D3: production-style scorecards

Implement scorecards for:

- task success
- latency
- token cost
- retrieval overhead
- bad-edit rate
- unsafe-action rate
- verifier lift
- resume reliability

Production questions answered:

- which harness settings are actually production-worthy?

Success criteria:

- every major experiment ends with a scorecard and recommendation memo

## Target Set E: Long-Context Systems and Inference Efficiency

### Target E1: cache policy simulator

Implement:

- baseline cache policy
- heuristic eviction
- lookahead-style eviction proxy
- metrics for memory and fidelity

Production questions answered:

- which cache policy provides the best quality/cost tradeoff for long sessions?

Success criteria:

- long-sequence replay is reproducible
- memory and quality proxies are captured

### Target E2: compressed-history memory prototype

Implement:

- compressed history blocks
- local raw-window retention
- retrieval over compressed plus local memory

Production questions answered:

- can compressed history preserve enough information for long-context tasks?
- how much local raw context must be retained?

Success criteria:

- compressed-history versus full-history tradeoffs are measurable

### Target E3: sparse index reuse prototype

Implement:

- reusable sparse index structures
- index rebuild versus reuse comparisons
- layer or stage reuse experiments

Production questions answered:

- when does sparse index reuse materially reduce long-context cost?

Success criteria:

- at least one reusable-index variant beats rebuild-every-time baselines on a meaningful proxy

### Target E4: serving-stack benchmark memo

Implement:

- kernel and stack compatibility matrix
- FlashAttention-style benchmark memo
- recommended serving upgrade path

Production questions answered:

- what should the serving stack adopt versus leave alone?

Success criteria:

- a benchmark-and-adoption memo exists even if no kernel is implemented locally

## Target Set F: Reduced Architecture Prototypes

### Target F1: concept selection gate

Build reduced prototypes only for concepts with cheap learning value, for example:

- compressed attention
- hybrid local/global context strategies
- compressed-history memory
- sparse access patterns

Production questions answered:

- which architecture ideas are worth a deeper sandbox investment?

Success criteria:

- each concept gets an isolated memo, not a bundled mega-experiment

### Target F2: promotion path into architecture lane

Connect promising concepts to:

- `code/architecture-advances-2026/`

Production questions answered:

- which papers from `LLMDevelopments.pdf` deserve implementation beyond the harness layer?

Success criteria:

- at least one concept is promoted into the architecture sandbox with a benchmark plan

## Target Set G: Production Adoption Layer

### Target G1: coding-agent integration

Adopt validated ideas into:

- `projects/coding-agent-v1/`

Candidate adoptions:

- retrieval default
- context-loading default
- verifier default
- handoff artifact contract
- long-horizon eval pack

Success criteria:

- the coding agent gets better by measured standards, not by intuition

### Target G2: decision memos

Produce memos for:

- what to adopt now
- what to keep experimental
- what to reject
- what to revisit later

Success criteria:

- the repo has explicit adoption decisions, not just raw experiment outputs

## End-to-End Completion Standard

This track is complete only when:

1. the repo has reusable harness and eval components for retrieval, reasoning, and long-context experiments
2. the repo can run benchmarked comparisons across multiple policies and presets
3. at least one long-context systems idea from the PDF has a working reduced prototype
4. `projects/coding-agent-v1/` has adopted the winning harness defaults
5. the repo contains decision memos that explain what was promoted, deferred, or rejected

## Immediate First Build Order

1. retrieval adapter layer
2. context assembly and repo-instruction loading
3. verifier and multi-attempt planning
4. CLI benchmark pack and scorecards
5. asynchronous handoff artifacts
6. long-context cache and compressed-history prototypes
7. coding-agent-v1 adoption pass
