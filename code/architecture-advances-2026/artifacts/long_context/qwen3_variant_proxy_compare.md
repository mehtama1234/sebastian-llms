# Long-Context Variant Proxy Report

## Bottom line
- Best proxy quality at the longest context: `mhc` (0.999).
- Lowest KV footprint at the longest context: `history_compression` (998244352 bytes, saving ratio 0.787).
- Best memory-aware quality tradeoff at the longest context: `compressed_attention` (0.955 proxy quality, 2348810240 KV bytes).

## Longest Context Ranking

| Variant | Proxy Quality | Proxy Pass Rate | KV Bytes | KV Saving Ratio | Total Params |
|---|---:|---:|---:|---:|---:|
| `mhc` | 0.999 | 1.000 | 4697620480 | 0.000 | 629157888 |
| `per_layer_embeddings` | 0.999 | 1.000 | 4697620480 | 0.000 | 4953399296 |
| `baseline` | 0.995 | 1.000 | 4697620480 | 0.000 | 596041728 |
| `attention_budgeting` | 0.980 | 1.000 | 4697620480 | 0.000 | 566681600 |
| `kv_sharing` | 0.975 | 1.000 | 2348810240 | 0.500 | 566681600 |
| `compressed_attention` | 0.955 | 1.000 | 2348810240 | 0.000 | 507961344 |
| `history_compression` | 0.934 | 0.750 | 998244352 | 0.787 | 607051776 |

## All Buckets

| Filler Repeats | Variant | Proxy Quality | Proxy Pass Rate | KV Bytes | KV Saving Ratio |
|---:|---|---:|---:|---:|---:|
| 32 | `attention_budgeting` | 0.980 | 1.000 | 4697620480 | 0.000 |
| 32 | `baseline` | 0.995 | 1.000 | 4697620480 | 0.000 |
| 32 | `compressed_attention` | 0.955 | 1.000 | 2348810240 | 0.000 |
| 32 | `history_compression` | 0.975 | 1.000 | 998244352 | 0.787 |
| 32 | `kv_sharing` | 0.975 | 1.000 | 2348810240 | 0.500 |
| 32 | `mhc` | 0.999 | 1.000 | 4697620480 | 0.000 |
| 32 | `per_layer_embeddings` | 0.999 | 1.000 | 4697620480 | 0.000 |
| 64 | `attention_budgeting` | 0.980 | 1.000 | 4697620480 | 0.000 |
| 64 | `baseline` | 0.995 | 1.000 | 4697620480 | 0.000 |
| 64 | `compressed_attention` | 0.955 | 1.000 | 2348810240 | 0.000 |
| 64 | `history_compression` | 0.975 | 1.000 | 998244352 | 0.787 |
| 64 | `kv_sharing` | 0.975 | 1.000 | 2348810240 | 0.500 |
| 64 | `mhc` | 0.999 | 1.000 | 4697620480 | 0.000 |
| 64 | `per_layer_embeddings` | 0.999 | 1.000 | 4697620480 | 0.000 |
| 128 | `attention_budgeting` | 0.980 | 1.000 | 4697620480 | 0.000 |
| 128 | `baseline` | 0.995 | 1.000 | 4697620480 | 0.000 |
| 128 | `compressed_attention` | 0.955 | 1.000 | 2348810240 | 0.000 |
| 128 | `history_compression` | 0.953 | 1.000 | 998244352 | 0.787 |
| 128 | `kv_sharing` | 0.975 | 1.000 | 2348810240 | 0.500 |
| 128 | `mhc` | 0.999 | 1.000 | 4697620480 | 0.000 |
| 128 | `per_layer_embeddings` | 0.999 | 1.000 | 4697620480 | 0.000 |
| 256 | `attention_budgeting` | 0.980 | 1.000 | 4697620480 | 0.000 |
| 256 | `baseline` | 0.995 | 1.000 | 4697620480 | 0.000 |
| 256 | `compressed_attention` | 0.955 | 1.000 | 2348810240 | 0.000 |
| 256 | `history_compression` | 0.934 | 0.750 | 998244352 | 0.787 |
| 256 | `kv_sharing` | 0.975 | 1.000 | 2348810240 | 0.500 |
| 256 | `mhc` | 0.999 | 1.000 | 4697620480 | 0.000 |
| 256 | `per_layer_embeddings` | 0.999 | 1.000 | 4697620480 | 0.000 |

## Context
- Baseline config: `/home/manishmehta/ui-projects/sebastian-llms/code/architecture-advances-2026/configs/qwen3-baseline.json`
- Variant configs: `6`
- Filler repeats: `[32, 64, 128, 256]`
- Cases per length: `2`
- Sweep runs: `2`
- Case result count: `112`
- This is a same-cases proxy comparison surface, not a real trained-model quality benchmark.
- It keeps the synthetic retrieval cases fixed across variants and uses architecture-aware proxy scoring.
- Use it to compare directional quality-vs-memory tradeoffs before investing in heavier training or finetuning work.
