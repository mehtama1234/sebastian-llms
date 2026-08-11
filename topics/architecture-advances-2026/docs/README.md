# LLM Architecture Advances 2026

Canonical topic folder for `LLMArchitectureAdvances2026.pdf`.

Source document:

- `../../LLMArchitectureAdvances2026.pdf`

## Scope

This topic is narrower than the filename suggests. The paper is mainly about long-context efficiency changes in recent open-weight LLMs, not a full survey of all 2026 architecture work.

The core ideas are:

1. `KV sharing` in Gemma 4 to shrink KV-cache memory by reusing K/V tensors across layers.
2. `Per-layer embeddings (PLE)` in Gemma 4 to add token-specific capacity without paying the full compute cost of a larger dense stack.
3. `Attention budgeting` in Laguna XS.2, where different layers get different query-head budgets.
4. `Compressed Convolutional Attention (CCA)` in ZAYA1-8B, which performs attention directly in compressed latent space.
5. `mHC + CSA/HCA` in DeepSeek V4, combining wider residual pathways with more aggressive long-context attention compression.

## Why this matters

The paper's unifying claim is simple:

> Long-context cost is now a first-order architecture problem because reasoning models and agent systems keep many tokens alive for longer.

## End-to-End Goal

Build a small but serious LLM architecture research lab around long-context efficiency, where we can implement modern ideas like KV sharing, attention budgeting, compressed attention, and DeepSeek-style residual/history mechanisms, compare them against a strong reference like `Qwen/Qwen3-0.6B`, and end with a working, evidence-backed architecture we would actually use for our own agent and reasoning workloads.

The deliverable is not a summary of papers. The deliverable is:

- a clean baseline model we own end to end
- architecture variants we can switch on and off
- a measurement harness for memory, latency, and long-context quality
- a reference track against `Qwen/Qwen3-0.6B`
- a final recommendation about which ideas are worth carrying forward

Success means we can answer, with code and measurements instead of hype:

- how much KV sharing saves
- how much quality it costs
- whether attention budgeting is a real systems win
- whether compressed attention is worth its extra complexity
- which design is best for our own agent and reasoning use cases

That means the implementation work should focus on:

- KV-cache size
- prefill and decode FLOPs
- memory bandwidth
- context-length scaling
- accuracy degradation from approximation

## Folder map

- [kv-sharing.md](./kv-sharing.md): cross-layer KV reuse and how to prototype it
- [per-layer-embeddings.md](./per-layer-embeddings.md): Gemma-style PLE path and what it changes
- [attention-budgeting.md](./attention-budgeting.md): layer-wise query-head budgets
- [compressed-attention.md](./compressed-attention.md): CCA and related compressed-attention experiments
- [compressed-attention-promotion-goal.md](./compressed-attention-promotion-goal.md): the next end-to-end milestone for turning the current winner into a promotion-ready architecture decision
- [deepseek-v4.md](./deepseek-v4.md): mHC plus CSA/HCA as the most aggressive design in the paper
- [implementation-roadmap.md](./implementation-roadmap.md): what to build first, in what order

## Working position

We should not try to reproduce full production models from the paper.

We should implement reduced, inspectable prototypes of each concept:

1. one change at a time
2. on a small decoder-only baseline
3. with explicit memory and latency measurements
4. with ablations against a clean baseline

That is the only realistic way to learn which ideas are useful versus merely interesting.
