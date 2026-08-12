# llm-developments-2026

A runnable, deterministic experiment harness that turns the "build now" list from
`LLMDevelopments.pdf` into measured policy decisions.

It replays one fixed synthetic repo benchmark under many harness configurations
and scores the tradeoffs the 2026 papers argue about:

| Production question | Papers | Axis in this lane |
| --- | --- | --- |
| Is lexical search enough, or do you need vector / hybrid / sparse indexing? | *Is Grep All You Need?*, sparse-attention retrieval papers | `retrieval_mode` = lexical / vector / hybrid / sparse |
| Should tool results stay inline or come back as pointers? | *Coding Agents Are Effective Long-Context Processors* | `context_policy` = inline_full / inline_snippet / pointer |
| Do repo instruction files help or just add token drag? | *Evaluating AGENTS.md* | `instruction_mode` = none / root / hierarchical |
| Can a cheap verifier stop the model from bluffing, and can a meta-verifier audit the grader? | *Learning to Self-Verify*, process-reward / verifier papers | `verifier_enabled`, `meta_verifier_enabled`, `max_retries` |
| Do parallel / shared / retried attempts beat one shot? | *PaCoRe*, *Share More, Search Less* | `candidate_count`, `share_evidence` |

## Why a synthetic substrate

Like the sibling `architecture-advances-2026` lane, the deliverable is a
**repeatable comparison of policies**, not a hardware or frontier-model quality
claim. The corpus, retrieval scores, recall flakiness, and bluffing are all
deterministic, so a run is fully reproducible and the *direction* of each tradeoff
is trustworthy. Every scorecard and memo says this in its own notes. The retrieval
duality is a deliberate caricature (the concept-space embedding is blind to exact
identifiers; lexical is blind to synonyms) so the lexical-vs-vector decision is
decisive and testable.

## What is real vs simulated

- **Real:** the harness config space, retrieval modes + RRF fusion, the sparse
  selector-plus-rerank path, context assembly and token accounting,
  instruction-loading coverage/cost, multi-attempt selection,
  verifier/meta-verifier control flow, stage-level failure labels, and the
  scorecard/decision-memo pipeline. These are the reusable production seams.
- **Simulated (near-oracle):** the model and the final truth signal. The
  verifier is still almost-perfect at grounding, so the verifier lift it reports
  is an **upper bound**. What changed is the shape of the interface: the
  verifier now emits a structured judgment and the meta-verifier audits whether
  that judgment matches the actual failure stage.

## Layout

```
src/llm_dev_2026/
  config.py        HarnessConfig — the serializable policy space
  benchmark_schema.py typed real-task benchmark schema
  benchmark_loader.py versioned benchmark manifest loader
  task_pack.py     task slicing by repo / class / difficulty / long-context
  provider.py      provider interface plus deterministic local and OpenAI-backed providers
  real_retrieval.py lexical, sparse, and task-aware repo-chunk retrieval over real workspace files
  runtime.py       real-task attempt artifact builder with gold-span or retrieval-backed context
  real_benchmark_runtime.py local readiness audit for real benchmark tasks
  real_task_verifier.py verifier/meta-verifier scoring over real-task attempt artifacts
  real_scorecard.py aggregate scorecards over verified real-task runs
  real_experiment.py real-manifest experiment runner and report builder
  real_policy_experiment.py comparative real-task policy matrix and scorecard deltas
  text.py          tokenizer, IDF, concept-space embedding
  corpus.py        synthetic repo + scenario pack (evidence placement, difficulty)
  retrieval.py     lexical / vector / hybrid / sparse retrieval + ops accounting
  context.py       inline_full / inline_snippet / pointer assembly + token budget
  instructions.py  none / root / hierarchical guidance loading + cost
  model.py         deterministic attempt: recall flakiness, grounding, bluffing
  verifier.py      structured grounding verifier
  meta_verifier.py verifier-auditor that checks the grader's coherence
  harness.py       orchestrates retrieval -> context -> attempts -> verify/meta-verify/escalate
  scorecard.py     production scorecards + directional comparison
  experiment.py    the default config matrix + comparison plan
  memo.py          rule-based adoption decisions
  cli.py / scorecard_cli.py / memo_cli.py / real_benchmark_cli.py / real_task_cli.py / real_task_verify_cli.py / real_experiment_cli.py / real_policy_experiment_cli.py
```

## Run it

```bash
python -m venv .venv && .venv/bin/pip install numpy pytest
.venv/bin/python -m pytest -q                      # 77 tests

.venv/bin/python -m llm_dev_2026.cli               # scorecard table + comparisons
.venv/bin/python -m llm_dev_2026.scorecard_cli     # scorecards only
.venv/bin/python -m llm_dev_2026.memo_cli          # adoption memo (markdown)
.venv/bin/python -m llm_dev_2026.real_benchmark_cli ../evals/datasets/real-repos/sample-benchmark.json
.venv/bin/python -m llm_dev_2026.real_task_cli ../evals/datasets/real-repos/sample-benchmark.json topics.inspect.deepseek_architecture_lane
.venv/bin/python -m llm_dev_2026.real_task_cli ../evals/datasets/real-repos/sample-benchmark.json topics.inspect.deepseek_architecture_lane --provider openai --model gpt-5.6
.venv/bin/python -m llm_dev_2026.real_task_verify_cli ../evals/datasets/real-repos/sample-benchmark.json topics.inspect.deepseek_architecture_lane --skip-validation
.venv/bin/python -m llm_dev_2026.real_experiment_cli ../evals/datasets/real-repos/sample-benchmark.json --provider local --evidence-source retrieval --retrieval-mode lexical --skip-validation
.venv/bin/python -m llm_dev_2026.real_policy_experiment_cli ../evals/datasets/real-repos/sample-benchmark.json --quiet
.venv/bin/python -m llm_dev_2026.real_policy_memo ../evals/datasets/real-repos/sample-benchmark.json --artifact-md artifacts/reports/real-retrieval-policy-memo.md
.venv/bin/python -m llm_dev_2026.real_retrieval_slice_report ../evals/datasets/real-repos/sample-benchmark.json --artifact-md artifacts/reports/real-retrieval-slice-report.md
.venv/bin/python -m llm_dev_2026.cli --out artifacts/report.json
```

## Coverage against `detailed-implementation-targets.md`

- **Implemented now:** A1 retrieval adapter, A2 context assembly + pressure, A3
  repo-instruction loading, B1 multi-attempt planning, B2 verifier layer, B3
  stop/retry/escalate policy, C1 harness schema, C2 task-class labels, D1 CLI
  scenario pack, D2 stage-level evaluation, D3 production scorecards, the
  first Workstream 1 scaffold for real benchmark manifests, and a real-task
  runtime/provider seam that emits attempt artifacts from local evidence or an
  OpenAI-backed Responses API provider and scores them through verifier plus meta-verifier, then aggregates them into real-task scorecards and compares gold-span, lexical-retrieval, sparse-retrieval, and task-aware-retrieval variants.

As of Wednesday, August 12, 2026, the widened 15-task real benchmark sample recommends `lexical` as the pooled real-task retrieval default. The supporting artifacts are `artifacts/reports/real-retrieval-policy-memo.md` and `artifacts/reports/real-retrieval-slice-report.md`.
- **Next:** expand the manifest beyond the sample pack, widen the comparative matrix beyond instruction/validation/retrieval variants, add stronger reranking and retrieval diagnostics, and then run real benchmark execution over live repos at useful scale.
  simulators (some already prototyped in `architecture-advances-2026`), F/G
  promotion into `projects/coding-agent-v1/` once the winning defaults are locked.

The current committed run is summarized in
`../projects/experiment-findings.md`.
