# KV Sharing

## What the paper says

Gemma 4 E2B/E4B reuse K/V tensors across layers instead of recomputing them in every attention layer.

Important detail:

- later layers still compute their own `Q`
- later layers reuse earlier layers' `K` and `V`
- sharing happens within the same attention type
  - sliding-window layers share with earlier sliding-window layers
  - full-attention layers share with earlier full-attention layers

The point is to reduce KV-cache memory and memory traffic at long context lengths.

## What changes architecturally

Baseline:

- every layer has its own `Wq`, `Wk`, `Wv`
- every layer stores its own K/V cache

KV-sharing variant:

- every layer still has its own `Wq`
- only selected layers own `Wk` and `Wv`
- later layers read K/V from the most recent compatible source layer

## Expected benefit

- smaller KV cache
- less K/V projection compute in shared layers
- better long-context feasibility on small hardware

## Expected cost

- lower capacity
- possible quality loss because layers no longer get fully independent K/V projections

## Implementation target

Build this first as the simplest concept from the paper.

Prototype shape:

1. small decoder-only transformer baseline
2. grouped-query or multi-query attention baseline
3. config flag for `kv_source_layer`
4. two modes:
   - `none`: standard per-layer K/V
   - `reuse_previous_same_type`: cross-layer reuse

## Questions to answer in code

- How much KV memory is saved as context length grows?
- What decode-time speedup, if any, appears in practice?
- How much perplexity or task quality is lost?
- Does sharing every other layer work better than sharing the whole tail?

## Must-have ablations

- no sharing
- share every 2 layers
- share every 4 layers
- tail-sharing only
- full-attention and sliding-window groups separated
