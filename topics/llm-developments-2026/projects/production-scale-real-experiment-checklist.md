# Production-Scale Real Experiment Checklist

This document turns the current `llm-developments-2026` lab into a concrete build program for a real production experiment.

The current harness is already useful because its control flow is real:

- retrieval mode selection
- context assembly
- instruction loading
- verifier-backed retry and escalation
- scorecards and comparison logic

What is not yet real enough for a production decision is:

- the benchmark substrate
- the model execution path
- the retrieval stack
- the verifier truth source
- the experiment operations layer

The goal of this checklist is to close that gap in a disciplined order.

## End State

The track is complete when this repo can run the same harness shape against:

- real repositories
- real coding-agent tasks
- real retrieval indexes
- real model calls
- real verifier signals
- real execution-based and human-backed grading

And then answer, with evidence:

1. Which retrieval stack should be default: lexical, hybrid, or sparse shortlist plus rerank?
2. When does verifier-backed retry improve real task success enough to justify latency?
3. When does a meta-verifier reduce bad verifier decisions enough to keep?
4. Which harness defaults should be promoted into `coding-agents/v1/`?

## Workstreams

## Workstream 1: Real Benchmark Substrate

### Outcome

Replace the synthetic benchmark in `code/src/llm_dev_2026/corpus.py` with a versioned real-task benchmark pack.

### Build

- Add `code/src/llm_dev_2026/benchmark_schema.py`
  - typed task schema
  - typed repo schema
  - typed evidence schema
  - typed validation schema
- Add `code/src/llm_dev_2026/benchmark_loader.py`
  - load benchmark manifests
  - validate schema
  - resolve repo snapshots
- Add `code/src/llm_dev_2026/task_pack.py`
  - task grouping
  - slice filters
  - difficulty buckets
- Add `evals/datasets/real-repos/`
  - benchmark manifest files
  - task definitions
  - grading metadata

### Required task fields

- `task_id`
- `repo_id`
- `repo_commit`
- `task_class`
- `prompt`
- `expected_artifact_type`
- `allowed_tools`
- `gold_files`
- `gold_evidence_spans`
- `validation_mode`
- `difficulty`
- `long_context`
- `notes`

### Validation modes to support

- `tests`
- `lint`
- `typecheck`
- `build`
- `diff_review`
- `human_review`
- `mixed`

### First milestone

- 25 to 50 real tasks across 3 repos
- at least 4 task classes
- at least 10 tasks with executable validation
- at least 10 tasks where retrieval quality materially matters

## Workstream 2: Real Model Execution

### Outcome

Replace the simulated attempt path in `code/src/llm_dev_2026/model.py` with real model-backed attempts and durable traces.

### Build

- Add `code/src/llm_dev_2026/runtime.py`
  - orchestrate live model attempts
  - normalize attempt outputs
- Add `code/src/llm_dev_2026/provider.py`
  - model provider interface
  - local stub provider
  - live provider adapter
- Add `code/src/llm_dev_2026/trace.py`
  - attempt trace schema
  - tool trace schema
  - retrieval trace schema
- Add `code/src/llm_dev_2026/cache.py`
  - request cache
  - artifact cache
  - deterministic replay hooks

### Attempt artifact contract

Each attempt should capture:

- prompt
- retrieved context
- instruction files loaded
- model output
- cited evidence
- tool calls
- patch or final answer
- stdout/stderr if execution happened
- token counts
- latency
- stop reason

### First milestone

- one provider wired into the existing harness
- deterministic artifact logging for every scenario run
- replayable run from stored traces without re-calling the model

## Workstream 3: Production Retrieval Stack

### Outcome

Turn `code/src/llm_dev_2026/retrieval.py` from a teaching implementation into a real retrieval experiment lane.

### Build

- Add `code/src/llm_dev_2026/chunking.py`
  - file chunking
  - symbol chunking
  - overlap rules
- Add `code/src/llm_dev_2026/indexes.py`
  - lexical index
  - embedding index
  - sparse selector index
- Add `code/src/llm_dev_2026/rerank.py`
  - exact rerank
  - reciprocal-rank fusion
  - learned rerank hook
- Add `code/src/llm_dev_2026/retrieval_eval.py`
  - gold evidence recall
  - shortlist recall
  - path precision
  - per-task retrieval diagnostics

### Retrieval modes to support

- lexical
- vector
- hybrid
- sparse shortlist plus exact rerank

### Real retrieval features to add

- path-aware priors
- symbol-aware retrieval
- import/call graph expansion
- chunk budget controls
- rerank depth controls
- query reformulation variants

### Production metrics

- gold file recall at `k`
- gold evidence span recall at `k`
- shortlist recall for sparse mode
- rerank lift over first-stage retrieval
- retrieval latency
- retrieval storage size
- retrieval token contribution to final prompt

### First milestone

- real indexing over one repo snapshot
- retrieval eval on a gold-labeled task slice
- scorecard showing lexical vs hybrid vs sparse

## Workstream 4: Real Verifier Stack

### Outcome

Turn the current structured verifier interface into a real multi-layer verifier system.

### Build

- Extend `code/src/llm_dev_2026/verifier.py`
  - verifier routing
  - verifier aggregation
  - confidence calibration
- Extend `code/src/llm_dev_2026/meta_verifier.py`
  - disagreement audit path
  - verifier correction path
- Add `code/src/llm_dev_2026/execution_verifier.py`
  - test pass/fail
  - lint and typecheck checks
  - build status checks
- Add `code/src/llm_dev_2026/grounding_verifier.py`
  - cited-span validation
  - unsupported-claim checks
- Add `code/src/llm_dev_2026/policy_verifier.py`
  - unsafe action checks
  - instruction and permission checks

### Verifier outputs must include

- `accepted`
- `score`
- `confidence`
- `failure_stage`
- `failure_type`
- `critique`
- `evidence_refs`
- `repair_hint`

### Meta-verifier job

The meta-verifier should audit whether the verifier:

- missed a real failure
- over-rejected a correct output
- produced a shallow critique
- was overconfident
- was inconsistent with executable truth

### First milestone

- execution verifier plus grounding verifier working together
- one disagreement audit report
- verifier precision and recall measured on a reviewed slice

## Workstream 5: Real Scorecards and Evaluation

### Outcome

Upgrade the current scorecard layer so it can drive a real product decision.

### Build

- Extend `code/src/llm_dev_2026/scorecard.py`
  - verifier precision/recall
  - meta-verifier correction rate
  - retrieval recall metrics
  - pass@k metrics
  - tail latency metrics
- Add `code/src/llm_dev_2026/stats.py`
  - confidence intervals
  - paired comparisons
  - bootstrap summaries
- Add `code/src/llm_dev_2026/review_export.py`
  - export disputed runs
  - export review bundles

### Metrics that must exist before promotion decisions

- true task success
- false success rate
- bad-edit rate
- verifier precision
- verifier recall
- meta-verifier correction rate
- gold evidence recall
- shortlist recall
- mean latency
- p95 latency
- mean token cost
- mean tool cost
- escalation rate
- repeat-run stability

### First milestone

- one machine-readable report with quality, cost, and reliability together
- one paired comparison between baseline and verifier-backed multi-attempt mode

## Workstream 6: Experiment Operations

### Outcome

Make runs reproducible, resumable, and reviewable.

### Build

- Add `code/src/llm_dev_2026/run_manifest.py`
  - benchmark version
  - model version
  - prompt version
  - retrieval config
  - verifier config
  - runtime environment
- Add `code/src/llm_dev_2026/artifacts.py`
  - artifact paths
  - trace bundles
  - review bundles
- Add `code/src/llm_dev_2026/resume.py`
  - interrupted run recovery
  - partial-run completion
- Add `code/scripts/run_real_benchmark.sh`
- Add `code/scripts/run_review_slice.sh`
- Add `code/scripts/run_retrieval_eval.sh`

### Run artifacts required

- config snapshot
- benchmark snapshot
- raw traces
- verifier outputs
- grading outputs
- summary report
- error log

### First milestone

- resume a stopped benchmark run
- regenerate the final scorecard from stored artifacts

## Workstream 7: Human Review Loop

### Outcome

Create a lightweight review system for cases automation cannot settle.

### Build

- Add `code/src/llm_dev_2026/review_schema.py`
  - human rubric schema
  - reviewer decision schema
- Add `code/src/llm_dev_2026/review_queue.py`
  - sample disputed runs
  - sample verifier disagreements
  - sample sparse-retrieval misses
- Add `evals/review-rubrics/`
  - correctness rubric
  - grounding rubric
  - usefulness rubric
  - safety rubric

### Human review should focus on

- verifier false positives
- verifier false negatives
- sparse shortlist misses
- high-confidence wrong outputs
- outputs that pass tests but look semantically wrong

### First milestone

- 20 to 30 reviewed cases
- one calibration memo from reviewer findings

## Data Contracts

## Benchmark contract

Each task record should be serializable and versioned. It must be possible to rerun the exact task later against a different harness configuration.

## Attempt contract

Each attempt record must preserve enough detail to explain:

- what was retrieved
- what was shown to the model
- what the model said
- what tools ran
- why the verifier accepted or rejected it

## Review contract

Each human-reviewed case must preserve:

- task id
- attempt id
- outputs shown to reviewer
- rubric used
- final decision
- confidence
- free-text notes

## Promotion Gates

Do not promote a new default into `coding-agents/v1/` unless all of the following are true:

- it improves true task success or materially reduces false success
- its latency increase is understood and measured
- its verifier behavior is calibrated on a reviewed slice
- its failures are explainable from saved artifacts
- it survives a holdout task slice

## Recommended Build Order

1. Real benchmark schema and loader.
2. Real model attempt runtime and trace logging.
3. Real retrieval indexing and retrieval eval.
4. Execution verifier and grounding verifier.
5. Scorecard and statistics upgrades.
6. Run manifests, artifact bundles, and resume support.
7. Human review queue and calibration loop.
8. Promotion decision sweep against holdout tasks.

## First Real Milestone Definition

This repo reaches its first real milestone when it can do all of the following in one lane:

- run 25 to 50 real tasks across real repos
- use a live model through the existing harness interface
- compare lexical, hybrid, and sparse retrieval
- run execution plus grounding verification
- produce a scorecard with quality, cost, and latency
- export disputed cases for human review

At that point the lab stops being mainly illustrative and starts being a real production experiment system.
