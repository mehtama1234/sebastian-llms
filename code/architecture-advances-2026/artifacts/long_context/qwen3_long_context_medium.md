# Long-Context Sweep Report

## Bottom line
- Best mean pass rate: filler repeats `12` (1.000, stdev 0.000).
- Lowest estimated KV cache: filler repeats `8` (35094528 bytes).
- Fastest generated-token throughput: filler repeats `8` (0.539 tokens/s).

## Length Buckets

| Filler Repeats | Runs | Cases/Run | Mean Pass Rate | Pass Rate Stdev | Mean Elapsed ms | Elapsed Stdev | Mean Gen Tok/s | Mean Total Tok/s | Mean KV Cache Bytes |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 1 | 2 | 0.000 | 0.000 | 19391.46 | 0.00 | 0.539 | 16.363 | 35094528 |
| 12 | 1 | 2 | 1.000 | 0.000 | 27620.63 | 0.00 | 0.372 | 16.662 | 51437568 |

## Context
- Model: `Qwen/Qwen3-0.6B`
- Filler repeats: `[8, 12]`
- Cases per length: `2`
- Sweep runs: `1`
- Overall pass rate: `0.500` across `4` cases
- This sweep varies synthetic context length via filler repeats and records both retrieval accuracy and latency.
- Use it to see how quality and runtime change together as prompt length grows.
- Multiple sweep runs aggregate independent synthetic case draws so each length bucket is less anecdotal.
