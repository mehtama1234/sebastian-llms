# Long-Context Sweep Report

## Bottom line
- Best mean pass rate: filler repeats `8` (0.000, stdev 0.000).
- Lowest estimated KV cache: filler repeats `8` (35094528 bytes).
- Fastest generated-token throughput: filler repeats `8` (0.467 tokens/s).

## Length Buckets

| Filler Repeats | Runs | Cases/Run | Mean Pass Rate | Pass Rate Stdev | Mean Elapsed ms | Elapsed Stdev | Mean Gen Tok/s | Mean Total Tok/s | Mean KV Cache Bytes |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 2 | 1 | 0.000 | 0.000 | 19309.58 | 804.28 | 0.467 | 16.342 | 35094528 |

## Context
- Model: `Qwen/Qwen3-0.6B`
- Filler repeats: `[8]`
- Cases per length: `1`
- Sweep runs: `2`
- Overall pass rate: `0.000` across `2` cases
- This sweep varies synthetic context length via filler repeats and records both retrieval accuracy and latency.
- Use it to see how quality and runtime change together as prompt length grows.
- Multiple sweep runs aggregate independent synthetic case draws so each length bucket is less anecdotal.
