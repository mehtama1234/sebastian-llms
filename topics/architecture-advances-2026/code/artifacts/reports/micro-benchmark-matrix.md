# Micro Benchmark Matrix

## Summary
- Best mean runtime across the grid: `compressed_attention`.
- Best worst-case runtime across the grid: tie between `attention_budgeting`, `compressed_attention`.
- Lowest KV cache across the grid: tie between `compressed_attention`, `kv_sharing`.
- Grid cells: `6`.

## Variant Matrix

| Variant | Mean Ratio Across Grid | Median Ratio | Best Ratio | Worst Ratio | Ratio Range | Mean ms Across Grid | KV Cache Bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| `compressed_attention` | 0.893 | 0.873 | 0.793 | 1.081 | 0.289 | 9.008 | 2048 |
| `attention_budgeting` | 0.971 | 0.987 | 0.817 | 1.087 | 0.271 | 10.597 | 4096 |
| `history_compression` | 0.976 | 0.966 | 0.863 | 1.118 | 0.254 | 10.088 | 4096 |
| `kv_sharing` | 0.996 | 0.966 | 0.826 | 1.227 | 0.400 | 10.078 | 2048 |
| `mhc` | 1.185 | 1.218 | 1.020 | 1.277 | 0.257 | 12.840 | 4096 |
| `per_layer_embeddings` | 1.283 | 1.279 | 1.221 | 1.338 | 0.116 | 13.488 | 4096 |

## Benchmark Context
- Baseline: `micro-baseline`; batch sizes `[1, 2]`; seq lens `[4, 8, 16]`; warmup `1`; measured `3`; report runs `3`.
- This matrix sweeps the existing micro benchmark across batch size and sequence length.
- Use it to inspect directional scaling behavior across variants, not to claim optimized hardware performance.
