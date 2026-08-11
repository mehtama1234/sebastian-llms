# Attention Budgeting

## What the paper says

Laguna XS.2 varies attention capacity by layer instead of giving every layer the same attention budget.

The main mechanism highlighted in the paper is:

- fixed KV-head shape for compatibility
- different numbers of query heads per layer
- fewer query heads for expensive full-attention layers
- more query heads for cheaper sliding-window layers

## Core idea

Not every layer deserves the same spend.

If a layer already uses full attention over the whole context, it is expensive. Reducing its query-head count is one way to cap that cost while preserving some global access.

## Implementation target

Build a per-layer head-budget config on top of a hybrid attention model:

1. mixed attention pattern:
   - sliding-window layers
   - periodic full-attention layers
2. add `num_query_heads_per_layer`
3. keep KV heads fixed where possible

## What to test

- uniform heads baseline
- fewer heads on global layers
- more aggressive reduction on global layers
- maybe the reverse as a sanity check

## What to measure

- attention FLOPs by layer
- latency by layer
- memory usage
- long-context retrieval performance
- whether losing heads on global layers hurts more than expected

## Why this belongs in the implementation plan

This is a practical systems lever.
It is easier to implement than CSA/HCA and can expose whether layer-wise budgeting is worth the extra configuration complexity.
