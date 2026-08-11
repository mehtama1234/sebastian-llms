# Compressed Attention

## What the paper says

The paper covers two compressed-attention directions:

- `CCA` in ZAYA1-8B
- `CSA/HCA` in DeepSeek V4

They are not the same thing, but both try to make long-context attention cheaper by avoiding standard dense attention over full-width states.

## CCA in plain terms

CCA compresses `Q`, `K`, and `V`, performs attention directly in the compressed latent space, and then projects back up.

The paper also notes a convolutional mixing step on compressed `Q` and `K` to recover some expressiveness after compression.

## Why CCA matters

Compared with MLA-style approaches that mainly compress storage and later project into attention space, CCA tries to save both:

- KV-cache size
- attention compute

## Implementation target

We should not start with the full ZAYA block.

Start with three small variants:

1. baseline MHA or GQA
2. latent-KV compression only
3. compressed-space attention

Optional fourth step:

4. add 1D depthwise convolution over compressed `Q` and `K`

## Questions to answer

- How much of the gain comes from compression alone?
- Does compressed-space attention hurt quality more than latent-cache-only designs?
- Does cheap convolution recover enough quality to justify the added complexity?

## Relationship to DeepSeek V4

DeepSeek V4 goes further than "compressed attention" as one single mechanism. Its CSA/HCA design combines:

- compressed historical blocks
- different compression levels
- sparse access to selected history
- dense attention over more heavily compressed history
- recent uncompressed sliding-window tokens

That is powerful but too complex as a first implementation target.
