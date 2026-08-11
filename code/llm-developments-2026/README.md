# llm-developments-2026

A runnable, deterministic experiment harness that turns the "build now" list from
`LLMDevelopments.pdf` into measured policy decisions.

It replays one fixed synthetic repo benchmark under many harness configurations
and scores the tradeoffs the 2026 papers argue about:

| Production question | Papers | Axis in this lane |
| --- | --- | --- |
| Is lexical search enough, or do you need vector / hybrid? | *Is Grep All You Need?* | `retrieval_mode` = lexical / vector / hybrid |
| Should tool results stay inline or come back as pointers? | *Coding Agents Are Effective Long-Context Processors* | `context_policy` = inline_full / inline_snippet / pointer |
| Do repo instruction files help or just add token drag? | *Evaluating AGENTS.md* | `instruction_mode` = none / root / hierarchical |
| Can a cheap verifier stop the model from bluffing? | *Learning to Self-Verify* | `verifier_enabled`, `max_retries` |
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

- **Real:** the harness config space, retrieval modes + RRF fusion, context
  assembly and token accounting, instruction-loading coverage/cost, multi-attempt
  selection, retry/escalate control flow, stage-level failure labels, and the
  scorecard/decision-memo pipeline. These are the reusable production seams.
- **Simulated (near-oracle):** the model and the verifier. The verifier is an
  almost-perfect grounding check, so the verifier lift it reports is an **upper
  bound**. Swapping the simulated model/verifier for a real LLM call is a
  localized change in `model.py` / `verifier.py`.

## Layout

```
src/llm_dev_2026/
  config.py        HarnessConfig — the serializable policy space
  text.py          tokenizer, IDF, concept-space embedding
  corpus.py        synthetic repo + scenario pack (evidence placement, difficulty)
  retrieval.py     lexical / vector / hybrid retrieval + ops accounting
  context.py       inline_full / inline_snippet / pointer assembly + token budget
  instructions.py  none / root / hierarchical guidance loading + cost
  model.py         deterministic attempt: recall flakiness, grounding, bluffing
  verifier.py      grounding verifier
  harness.py       orchestrates retrieval -> context -> attempts -> verify/escalate
  scorecard.py     production scorecards + directional comparison
  experiment.py    the default config matrix + comparison plan
  memo.py          rule-based adoption decisions
  cli.py / scorecard_cli.py / memo_cli.py
```

## Run it

```bash
python -m venv .venv && .venv/bin/pip install numpy pytest
.venv/bin/python -m pytest -q                      # 37 tests

.venv/bin/python -m llm_dev_2026.cli               # scorecard table + comparisons
.venv/bin/python -m llm_dev_2026.scorecard_cli     # scorecards only
.venv/bin/python -m llm_dev_2026.memo_cli          # adoption memo (markdown)
.venv/bin/python -m llm_dev_2026.cli --out artifacts/report.json
```

## Coverage against `detailed-implementation-targets.md`

- **Implemented now:** A1 retrieval adapter, A2 context assembly + pressure, A3
  repo-instruction loading, B1 multi-attempt planning, B2 verifier layer, B3
  stop/retry/escalate policy, C1 harness schema, C2 task-class labels, D1 CLI
  scenario pack, D2 stage-level evaluation, D3 production scorecards.
- **Next:** A1 reranking, C3 async handoff artifacts, E cache/compression
  simulators (some already prototyped in `architecture-advances-2026`), F/G
  promotion into `projects/coding-agent-v1/` once the winning defaults are locked.

The current committed run is summarized in
`../../projects/llm-developments-2026/experiment-findings.md`.
