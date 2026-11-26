# Frontier architecture executive memo

Status: initial evidence memo, 2026-11-25

## Bottom line

The strongest public designs are not converging on one replacement for the
Transformer. They are splitting the old “keep and reread every token at every
layer” contract into different state paths: compressed or shared KV, recurrent
state, selected explicit history, sparse expert weights, and extra internal
depth. Each path saves a different resource and introduces a different failure
mode.

The first engineering decision should therefore be workload-specific:

- For memory-bound long context, start with cache ownership and representation
  accounting. GQA/shared KV changes stored bytes; it does not automatically
  reduce selection work or improve exact recall.
- For long-context retrieval, compare recurrent state against explicit selected
  reads. Recurrent state is fixed-size and updated every token; it cannot be
  assumed to preserve arbitrary distant tokens without a lookup path.
- For agentic decode, measure speculation acceptance and verification cost,
  not just the existence of MTP heads. Drafting helps only when accepted work
  repays proposal and verification overhead.
- For shared-weight depth, count layer applications separately from stored
  parameters and visible output tokens. Inkling's 24 stored layers becoming 48
  applications per token is more compute, not a free memory reduction.

The later controls make two boundaries explicit: Kimi K2 combines MLA with
large MoE routing, while Gemma 3 supplies a dense GQA/local-global reference.
Neither active-parameter count nor periodic full attention is a direct proxy
for deployment memory or task quality.

The later controls make two boundaries explicit: Kimi K2 combines MLA with
large MoE routing, while Gemma 3 supplies a dense GQA/local-global reference.
Neither active-parameter count nor periodic full attention is a direct proxy
for deployment memory or task quality.

## What is established now

1. Primary release material documents four distinct mechanisms: DeepSeek CSA2
   plus FP4/replay, Qwen DeltaNet plus QSA, Nemotron hybrid state plus native
   speculation, and Inkling looped shared-weight depth.
2. The existing lab's ignored local configuration fixtures were missing from
   this checkout. Reconstructed minimal fixtures now make the baseline summary
   and mechanism test surface runnable.
3. The new mechanism proxy reproduces the analytical GQA example: 32 layers,
   8 KV heads, width 128, BF16, and 131,072 tokens require 16 GiB before
   overhead. It also shows that shared-cache fresh selection and reused
   selection have identical storage but different index-work counts.
4. A deterministic 12-token distractor probe gives fresh selection both
   changing-query targets, while reused selection keeps the first query's
   indices: target hits fall from 2 to 1 while index work halves. This is a
   toy falsification control, not a quality claim about a trained indexer.

## What is not established

- No independent frontier checkpoint run has been performed.
- No local GPU, engine, throughput, energy, or task-quality measurement has
  been claimed.
- Vendor throughput and benchmark tables are not treated as matched workload
  evidence.
- Exact layer schedules, page layouts, routing traffic, and runtime state
  serialization remain unknown for several families.

## Next conclusion-changing experiment

Run a fixed-distractor long-context probe on a permitted small local model or
the toy harness: hold precision and sequence length constant; compare full
attention, shared KV with fresh selection, shared KV with reused selection, and
recurrent state plus periodic lookup. Record stored bytes, bytes touched,
selection work, state updates, exact late-token recall, and multi-turn state
handoff separately. That experiment would directly test whether the predicted
memory savings survive the retrieval and runtime costs.
