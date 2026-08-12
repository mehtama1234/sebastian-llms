# Architecture Advances 2026 Project Track

This project track converts `docs/architecture-advances-2026/` into buildable work.

Primary source:

- `../../LLMArchitectureAdvances2026.pdf`

Canonical docs:

- `../../docs/architecture-advances-2026/README.md`
- `./meaty-end-to-end-goal.md`
- `./indexer-vs-attention-goal.md`

## Goal

Implement reduced prototypes of the paper's main architecture ideas and measure their real tradeoffs.

## End State

The project is complete when we have:

- one baseline decoder-only model/harness for controlled architecture experiments
- one reference track using `Qwen/Qwen3-0.6B` for comparison and parity sanity checks
- one implementation path for each major paper concept
  - KV sharing
  - attention budgeting
  - per-layer embeddings
  - compressed attention
  - DeepSeek-inspired residual/history prototypes
- one repeatable evaluation setup for:
  - KV-cache memory
  - throughput and latency
  - long-context retrieval/reasoning quality
  - training stability
- one final decision memo that says which architecture changes we would actually keep

In plain terms: this track should end as an architecture experimentation platform, not a reading list.

## Workstreams

1. `kv-sharing-prototype`
2. `attention-budgeting-prototype`
3. `per-layer-embeddings-prototype`
4. `compressed-attention-prototype`
5. `deepseek-v4-inspired-prototypes`
6. `indexer-vs-attention`

## Delivery rule

Each workstream should produce:

- one clean baseline
- one concept toggle
- one ablation matrix
- one short decision memo saying whether the concept is worth carrying forward

## Current operating rule

The code workspace now has a layered decision stack, not just raw benchmark artifacts.

When new follow-up evidence lands, the canonical refresh step is:

`code/architecture-advances-2026/scripts/run_decision_stack.sh`

That one runner regenerates the current:

- concept scorecard
- decision audit
- review plan
- final architecture memo

So the project should treat that script as the authoritative "sync the decision layer" entrypoint rather than rerunning those reports by hand in an arbitrary order.
That includes cases where the same variant gets multiple focused follow-up assessments from different surfaces, such as training and long-context proxy checks.
