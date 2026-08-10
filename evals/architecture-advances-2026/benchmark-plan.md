# Benchmark Plan

## Baseline tasks

Use at least one task from each bucket:

1. `language modeling`
   - validation perplexity on held-out text
2. `long-context retrieval`
   - passkey retrieval
   - needle-in-haystack style insertion/recovery
3. `multi-hop context use`
   - synthetic tasks requiring information from distant positions

## Systems measurements

Measure for multiple context lengths:

- `4K`
- `16K`
- `64K`
- `128K` if hardware permits

For each, log:

- KV-cache memory
- total peak memory
- prefill throughput
- decode throughput
- tokens/sec

## Concept-specific checks

### KV sharing

- quality as sharing depth increases
- memory saved per sharing schedule

### Attention budgeting

- cost saved by shrinking heads on global layers
- quality drop on global retrieval tasks

### PLE

- quality at fixed effective compute
- whether added embedding parameters help small models more than larger ones

### Compressed attention

- quality versus compression ratio
- whether convolution recovers enough quality

### DeepSeek-inspired prototypes

- mHC stability compared with normal residual stream
- compressed-history retrieval quality versus context length

## Reporting format

Every run should end with a short matrix:

- baseline
- variant
- short-context quality
- long-context quality
- memory delta
- latency delta
- verdict
