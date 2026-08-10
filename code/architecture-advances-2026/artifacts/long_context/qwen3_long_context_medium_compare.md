# Long-Context Comparison

## Bottom line
- Best observed reference pass rate was at filler repeats `12` (1.000).
- Lowest projected KV-cache cost in this comparison is `kv_sharing` at filler repeats `12` (25718784 bytes).
- Fastest projected elapsed-ms in this comparison is `compressed_attention` at filler repeats `12` (22079.28 ms).

## Recommendation Layer
- Recommendations below only consider rows whose reference bucket pass rate is at least `0.500`.
- Best memory saver at acceptable quality: `kv_sharing` at filler repeats `12` with projected KV cache `25718784` bytes and reference pass rate `1.000`.
- Best projected speed at acceptable quality: `compressed_attention` at filler repeats `12` with projected elapsed `22079.28` ms.
- Best balanced compute choice at acceptable quality: `compressed_attention` at filler repeats `12` with FLOPs ratio `0.799` and projected KV saving `0.500`.

## Combined Table

| Filler Repeats | Ref Pass Rate | Ref Elapsed ms | Variant | Proj KV Bytes | Proj KV Saving | FLOPs Ratio | Proj Elapsed ms | Elapsed Delta ms | Owner Layers | Eff Head Dim |
|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0.000 | 19391.46 | `kv_sharing` | 17547264 | 0.500 | 0.933 | 18101.39 | -1290.08 | 14 | 128 |
| 8 | 0.000 | 19391.46 | `attention_budgeting` | 35094528 | 0.000 | 0.933 | 18091.31 | -1300.16 | 28 | 128 |
| 8 | 0.000 | 19391.46 | `compressed_attention` | 17547264 | 0.500 | 0.799 | 15501.07 | -3890.39 | 28 | 64 |
| 8 | 0.000 | 19391.46 | `per_layer_embeddings` | 35094528 | 0.000 | 1.067 | 20681.54 | 1290.08 | 28 | 128 |
| 12 | 1.000 | 27620.63 | `kv_sharing` | 25718784 | 0.500 | 0.933 | 25783.08 | -1837.55 | 14 | 128 |
| 12 | 1.000 | 27620.63 | `attention_budgeting` | 51437568 | 0.000 | 0.933 | 25768.73 | -1851.90 | 28 | 128 |
| 12 | 1.000 | 27620.63 | `compressed_attention` | 25718784 | 0.500 | 0.799 | 22079.28 | -5541.35 | 28 | 64 |
| 12 | 1.000 | 27620.63 | `per_layer_embeddings` | 51437568 | 0.000 | 1.067 | 29458.18 | 1837.55 | 28 | 128 |

## Notes
- Reference quality and reference latency come from the real Qwen sweep artifact.
- Variant costs are projected from the Qwen-shaped config family.
- Projected elapsed-ms is a compute-side estimate from config-level FLOP ratios, not a measured runtime.
