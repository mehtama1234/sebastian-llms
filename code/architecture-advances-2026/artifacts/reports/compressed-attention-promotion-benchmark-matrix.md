# Micro Benchmark Matrix

## Summary
- Best mean runtime across the grid: `history_compression`.
- Best worst-case runtime across the grid: `compressed_attention`.
- Lowest KV cache across the grid: `kv_sharing`.
- Grid cells: `12`.

## Variant Matrix

| Variant | Mean Ratio Across Grid | Median Ratio | Best Ratio | Worst Ratio | Ratio Range | Mean ms Across Grid | KV Cache Bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| `history_compression` | 0.921 | 0.880 | 0.732 | 1.301 | 0.569 | 2.488 | 4096 |
| `compressed_attention` | 0.981 | 1.000 | 0.833 | 1.105 | 0.271 | 3.321 | 4096 |
| `attention_budgeting` | 0.998 | 0.979 | 0.868 | 1.155 | 0.287 | 3.417 | 4096 |
| `kv_sharing` | 1.008 | 0.985 | 0.746 | 1.164 | 0.417 | 3.417 | 2048 |
| `per_layer_embeddings` | 1.175 | 1.172 | 1.018 | 1.457 | 0.439 | 4.074 | 4096 |
| `mhc` | 1.299 | 1.324 | 1.174 | 1.420 | 0.246 | 4.485 | 4096 |

## Benchmark Context
- Baseline: `micro-baseline`; batch sizes `[1, 2, 4]`; seq lens `[4, 8, 16, 32]`; warmup `1`; measured `3`; report runs `3`.
- This matrix sweeps the existing micro benchmark across batch size and sequence length.
- Use it to inspect directional scaling behavior across variants, not to claim optimized hardware performance.
