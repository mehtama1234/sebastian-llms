# Micro-scale architecture decision memo

## Bottom line
- Fastest variant on the aggregated micro benchmark: `kv_sharing` (0.821x baseline mean time, stdev 0.262).
- Lowest estimated FLOPs: `compressed_attention` (1998848).
- Lowest estimated KV cache: `kv_sharing` (4096 bytes).
- Most expensive timing direction on this aggregated micro setup: `per_layer_embeddings` (1.512x baseline mean time, stdev 0.339).

## Recommendations
- Use `kv_sharing` when the main constraint is KV-cache footprint rather than absolute lowest estimated FLOPs.
- Use `compressed_attention` when the main goal is reducing attention-side compute and KV storage together.
- Treat `per_layer_embeddings` as a capacity-increasing variant that likely needs stronger quality justification before adoption.

## Variant Matrix

| Variant | Mean Ratio vs Baseline | Ratio Stdev | Estimated FLOPs | KV Cache Bytes | KV Cache Delta |
|---|---:|---:|---:|---:|---:|
| `kv_sharing` | 0.821 | 0.262 | 2293760 | 4096 | -4096 |
| `attention_budgeting` | 0.822 | 0.246 | 2277376 | 8192 | 0 |
| `per_layer_embeddings` | 1.512 | 0.339 | 2686976 | 8192 | 0 |
| `compressed_attention` | 1.042 | 0.521 | 1998848 | 4096 | -4096 |

## Benchmark Context
- Baseline: `micro-baseline` with batch size `1`, sequence length `8`, warmup runs `1`, measured runs `5`, report runs `3`.
- This report aggregates multiple micro-scale NumPy benchmark runs against a shared baseline.
- Use it to compare directional tradeoffs across variants, not to make production hardware claims.
