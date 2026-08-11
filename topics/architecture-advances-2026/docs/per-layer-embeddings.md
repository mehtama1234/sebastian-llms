# Per-Layer Embeddings

## What the paper says

Gemma 4 E2B/E4B use per-layer embeddings (PLE) as a separate efficiency idea from KV sharing.

The paper's point:

- KV sharing reduces cache cost
- PLE adds token-specific capacity without making the repeated transformer stack as expensive as a much larger dense model

The hidden state gates a layer-specific embedding-derived residual update.

## What changes architecturally

Baseline:

- one token embedding path
- repeated transformer blocks

PLE variant:

- token IDs also produce layer-specific embedding slices
- each block receives its own slice
- each block adds a gated PLE residual update

So capacity moves partly into extra embedding tables instead of only scaling the repeated compute-heavy stack.

## Why this is interesting

This is not primarily a long-context trick.
It is a parameter-efficiency trick that changes where model capacity lives.

## Implementation target

Prototype a simplified PLE path:

1. normal token embedding
2. learned per-layer embedding table
3. projection into model dimension
4. per-layer gate from the block hidden state
5. residual add at the end of each block

## What to measure

- parameter count versus active compute
- training stability
- quality gain at fixed FLOPs
- whether PLE helps more on small models than medium ones

## Risks

- easy to overcomplicate the prototype
- may improve parameter count optics more than real quality
- likely interacts with training recipe strongly

## Position

Implement this after KV sharing.
It is conceptually clean, but harder to interpret than KV sharing because gains may come from capacity redistribution rather than obvious runtime savings.
