# Architecture Concept Scorecard

_Updated: 2026-08-09_

## Bottom line
- Default carry-forward concept: `compressed_attention` with long-context proxy quality `0.955` and training loss delta `-4.916`.
- Default systems sweep mean runtime ratio across the micro grid: `0.893` (worst cell `1.081`).
- Secondary keep set: `kv_sharing`.
- Exploratory-only set: `history_compression`, `mhc`.

## Concept Matrix

| Variant | Decision | Micro Runtime | Sweep Mean Ratio | Sweep Median Ratio | Sweep Worst Ratio | Micro KV Bytes | Long Proxy Quality | Long Pass Rate | Training Loss Delta | Training Loss Range | Consistent Loss | Training Speed Ratio | Consistent Speed |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `compressed_attention` | default | 1.013 | 0.893 | 0.873 | 1.081 | 4096 | 0.955 | 1.000 | -4.916 | 0.793 | true | 2.192 | false |
| `kv_sharing` | secondary | 1.054 | 0.996 | 0.966 | 1.227 | 4096 | 0.975 | 1.000 | -0.399 | 1.212 | false | 3.837 | false |
| `history_compression` | exploratory | 0.991 | 0.976 | 0.966 | 1.118 | 5120 | 0.934 | 0.750 | -1.767 | 3.762 | false | 2.173 | false |
| `mhc` | exploratory | 1.108 | 1.185 | 1.218 | 1.277 | 8192 | 0.999 | 1.000 | -3.961 | 0.583 | true | 1.255 | false |
| `attention_budgeting` | drop | 1.057 | 0.971 | 0.987 | 1.087 | 8192 | 0.980 | 1.000 | -1.363 | 1.551 | true | 0.603 | true |
| `per_layer_embeddings` | drop | 1.367 | 1.283 | 1.279 | 1.338 | 8192 | 0.999 | 1.000 | 0.000 | 0.000 | false | 0.545 | true |

## Coverage
- Micro baseline: `micro-baseline` with sequence length `8`.
- Long-context filler repeats: `[32, 64, 128, 256]`.
- Training matrix coverage: seq_lens `[8, 16]`, steps `[4]`, seeds `[17]`.
- Benchmark matrix coverage: batch sizes `[1, 2]`, seq_lens `[4, 8, 16]`, measured runs `3`, report runs `3`.
- This scorecard aligns systems, proxy long-context, and training evidence per architecture concept.
- Decision labels come from the final architecture memo so the per-concept rows match the current carry-forward call.
