# Prototype Roadmap

## Phase 0: baseline harness

Build or reuse a small decoder-only transformer training and inference harness with:

- configurable attention module
- configurable residual block
- memory/latency measurement hooks
- long-context synthetic tasks

## Phase 1: KV sharing

Build:

- per-layer K/V ownership map
- shared-cache reads
- compatibility check for attention type grouping

Exit criteria:

- measured KV-cache reduction
- quality comparison against baseline

## Phase 2: attention budgeting

Build:

- per-layer query-head config
- hybrid local/global attention schedule
- layer-wise FLOP report

Exit criteria:

- cost savings shown
- no catastrophic quality drop on retrieval-style tests

## Phase 3: PLE

Build:

- per-layer embedding path
- hidden-state gate
- residual injection point

Exit criteria:

- parameter/compute accounting is clear
- effect on training and quality is measurable

## Phase 4: compressed attention

Build:

- latent compressor
- compressed-space attention
- optional local convolution on compressed Q/K

Exit criteria:

- cache and FLOP savings measured
- quality tradeoff understood

## Phase 5: DeepSeek-inspired prototypes

Build separately:

- simplified mHC block
- simplified compressed-history memory

Exit criteria:

- each concept judged independently
- no combined prototype until isolated behavior is understood

## Phase 6: compressed-attention promotion pass

Build:

- a broader `compressed_attention` training follow-up across more seeds, steps, and sequence lengths
- a harder long-context evaluation lane for `compressed_attention`
- a wider systems sweep that compares `compressed_attention` against baseline and `kv_sharing`
- a refreshed decision memo that answers whether `compressed_attention` is ready for the next heavier experiment stage

Exit criteria:

- `compressed_attention` still looks like the best blended quality-preserving systems trade on broader evidence
- the repo can make a real promotion decision instead of relying on micro or proxy wins alone
