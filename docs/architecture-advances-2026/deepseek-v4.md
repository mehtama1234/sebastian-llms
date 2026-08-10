# DeepSeek V4

## What the paper says

The two highlighted DeepSeek V4 ideas are:

1. `mHC` for the residual pathway
2. `CSA/HCA` for long-context attention compression

The paper explicitly treats these as separate changes:

- `mHC` changes how information moves through residual streams
- `CSA/HCA` changes how long-context attention is stored and accessed

## mHC

Regular transformers have one residual stream.

Hyper-connections widen that into multiple interacting residual streams.
mHC keeps that idea but constrains the mixing so it behaves more stably.

The paper's interpretation:

- HC gives richer residual mixing
- mHC adds constraints so it scales more safely in larger/deeper models

## CSA/HCA

The paper describes this as a more aggressive long-context design than MLA.

High-level structure:

- sparse selection over compressed history blocks (`CSA`)
- dense attention over more heavily compressed blocks (`HCA`)
- uncompressed recent tokens through a sliding-window branch

This is a hybrid historical-memory design rather than one uniform attention rule.

## Implementation position

Do not attempt full DeepSeek V4 reproduction as the first pass.

Break it into two separate workstreams:

1. `mHC prototype`
   - widened residual streams
   - constrained mixing matrices
   - compare against normal residual stream
2. `history-compression prototype`
   - recent uncompressed window
   - compressed old-history memory
   - sparse retrieval over old blocks

## Why this decomposition matters

If we implement mHC and CSA/HCA together from day one, we will not know which part helps or hurts.

## Questions to answer

- Does multi-stream residual mixing help small models, or only larger ones?
- Can a simple compressed-history memory recover enough long-context retrieval quality?
- Where is the quality cliff as compression increases?
- Is the added systems complexity justified for our use cases?
