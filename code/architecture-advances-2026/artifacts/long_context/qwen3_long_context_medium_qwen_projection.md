# Long-Context Variant Projection

## Bottom line
- Reference quality comes from the real Qwen sweep artifact.
- Variant rows project KV-cache cost and a compute-scaled elapsed-ms estimate, not quality.

## Projected Buckets

| Filler Repeats | Reference Pass Rate | Variant | KV Ratio vs Baseline | FLOPs Ratio vs Baseline | Projected KV Bytes | Projected Saving Ratio | Projected Elapsed ms | Owner Layers | Effective Head Dim |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0.000 | `kv_sharing` | 0.500 | 0.933 | 17547264 | 0.500 | 18101.39 | 14 | 128 |
| 8 | 0.000 | `attention_budgeting` | 1.000 | 0.933 | 35094528 | 0.000 | 18091.31 | 28 | 128 |
| 8 | 0.000 | `compressed_attention` | 0.500 | 0.799 | 17547264 | 0.500 | 15501.07 | 28 | 64 |
| 8 | 0.000 | `per_layer_embeddings` | 1.000 | 1.067 | 35094528 | 0.000 | 20681.54 | 28 | 128 |
| 12 | 1.000 | `kv_sharing` | 0.500 | 0.933 | 25718784 | 0.500 | 25783.08 | 14 | 128 |
| 12 | 1.000 | `attention_budgeting` | 1.000 | 0.933 | 51437568 | 0.000 | 25768.73 | 28 | 128 |
| 12 | 1.000 | `compressed_attention` | 0.500 | 0.799 | 25718784 | 0.500 | 22079.28 | 28 | 64 |
| 12 | 1.000 | `per_layer_embeddings` | 1.000 | 1.067 | 51437568 | 0.000 | 29458.18 | 28 | 128 |

## Notes
- This is a cost-only projection anchored to the real Qwen sweep buckets.
- Projected KV-cache bytes use each variant's config-level KV ratio relative to the baseline config.
- Projected elapsed-ms uses each variant's estimated-FLOP ratio from the local numeric runtime.
- Reference pass rate and latency come from the real sweep artifact; projected quality is not claimed.
