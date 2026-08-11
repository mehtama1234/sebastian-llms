# Long-Context Variant Projection

## Bottom line
- Reference quality comes from the real Qwen sweep artifact.
- Variant rows project KV-cache cost and a compute-scaled elapsed-ms estimate, not quality.

## Projected Buckets

| Filler Repeats | Reference Pass Rate | Variant | KV Ratio vs Baseline | FLOPs Ratio vs Baseline | Projected KV Bytes | Projected Saving Ratio | Projected Elapsed ms | Owner Layers | Effective Head Dim |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0.000 | `kv_sharing` | 0.500 | 0.946 | 17547264 | 0.500 | 18343.27 | 2 | 16 |
| 8 | 0.000 | `attention_budgeting` | 1.000 | 0.939 | 35094528 | 0.000 | 18212.25 | 4 | 16 |
| 8 | 0.000 | `compressed_attention` | 0.500 | 0.824 | 17547264 | 0.500 | 15984.85 | 4 | 8 |
| 8 | 0.000 | `per_layer_embeddings` | 1.000 | 1.108 | 35094528 | 0.000 | 21487.84 | 4 | 16 |
| 12 | 1.000 | `kv_sharing` | 0.500 | 0.946 | 25718784 | 0.500 | 26127.62 | 2 | 16 |
| 12 | 1.000 | `attention_budgeting` | 1.000 | 0.939 | 51437568 | 0.000 | 25941.00 | 4 | 16 |
| 12 | 1.000 | `compressed_attention` | 0.500 | 0.824 | 25718784 | 0.500 | 22768.36 | 4 | 8 |
| 12 | 1.000 | `per_layer_embeddings` | 1.000 | 1.108 | 51437568 | 0.000 | 30606.64 | 4 | 16 |

## Notes
- This is a cost-only projection anchored to the real Qwen sweep buckets.
- Projected KV-cache bytes use each variant's config-level KV ratio relative to the baseline config.
- Projected elapsed-ms uses each variant's estimated-FLOP ratio from the local numeric runtime.
- Reference pass rate and latency come from the real sweep artifact; projected quality is not claimed.
