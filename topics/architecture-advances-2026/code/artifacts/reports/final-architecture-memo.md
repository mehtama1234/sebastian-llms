# Architecture Advances 2026 Final Decision Memo

_Updated: 2026-08-09_

## Bottom line
- Default carry-forward architecture: `compressed_attention`.
- Best micro runtime direction: `history_compression`.
- Best micro KV-memory direction: tie between `compressed_attention`, `kv_sharing`.
- Best mean systems-sweep runtime direction among carry-forward candidates: `compressed_attention`; best worst-case systems-sweep direction among carry-forward candidates: `compressed_attention`; lowest-KV systems-sweep direction among carry-forward candidates: tie between `compressed_attention`, `kv_sharing`.
- Longest-context proxy selector carry-forward pick: `compressed_attention`.
- Focused long-context proxy rerun for `compressed_attention` kept all cases passing while trading 0.500 KV-cache saving ratio against a proxy-quality delta of `-0.040`.
- Training matrix fastest trend variant: `per_layer_embeddings`; lowest final-loss trend variant: `compressed_attention`; lowest grad-delta trend variant: `attention_budgeting`; stable speed leader: `per_layer_embeddings`; stable loss leader: `compressed_attention`; finite across matrix: `attention_budgeting`, `compressed_attention`, `history_compression`, `kv_sharing`, `mhc`, `per_layer_embeddings`.
- Focused follow-up review priority variants: `kv_sharing`.

## Recommendations
- Keep `compressed_attention` as the default next heavier experiment candidate because it is the current long-context carry-forward winner and the strongest blended quality-preserving systems trade.
- Keep secondary branches for `kv_sharing` when the decision is dominated by a single constraint rather than the blended objective.
- Use the systems sweep as a second systems gate: `compressed_attention` currently averages 0.893x baseline across the sampled micro grid, with worst cell `1.081`.
- Do not promote `kv_sharing` beyond secondary until its systems-sweep worst cell drops below about 1.2x baseline or its quality gain clearly justifies the instability.
- Keep `mhc` exploratory only until a real quality benchmark shows enough gain to justify its higher complexity and no KV-memory win.
- Keep `history_compression` exploratory for explicitly old-token-dominated long-context work, not as the default path.
- Do not carry forward `attention_budgeting`, `per_layer_embeddings` as default candidates with current evidence.
- Use the training matrix as a stronger gate: prefer variants that stay finite across schedule/seed combinations and avoid variants whose win disappears under small training-shape changes.
- Use repeated and consistent training wins as a filter: the current stable loss leader is `compressed_attention`.
- Treat stable speed wins separately from mean speed wins: the current stable speed leader is `per_layer_embeddings`.
- Treat repeated matrix wins as stronger evidence than a single row: the current loss-trend leader is `compressed_attention`.
- Treat `kv_sharing` as a bounded secondary branch rather than a fully settled keep: follow-up evidence is mixed, but the weighted balance still favors `secondary` over `exploratory`.
- Focused follow-up review keeps `kv_sharing` secondary because the weighted evidence still favors the current label, even though a weaker surface points toward `exploratory`.
- Focused follow-up review demotes `history_compression` from secondary to exploratory until the stronger evidence gap is resolved.

## Carry Forward
- Default: `compressed_attention`
- Secondary: `kv_sharing`
- Exploratory: `mhc`, `history_compression`
- Drop for now: `attention_budgeting`, `per_layer_embeddings`

## Evidence Matrix

| Variant | Micro Runtime Ratio | Sweep Mean Ratio | Sweep Worst Ratio | Micro KV Bytes | Long-Context Pick | Runtime Pick | Memory Pick | Training Evidence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `attention_budgeting` | 1.057 | 0.971 | 1.087 | 8192 | false | false | false | true |
| `compressed_attention` | 1.013 | 0.893 | 1.081 | 4096 | true | false | false | true |
| `history_compression` | 0.991 | 0.976 | 1.118 | 5120 | false | true | false | true |
| `kv_sharing` | 1.054 | 0.996 | 1.227 | 4096 | false | false | true | true |
| `mhc` | 1.108 | 1.185 | 1.277 | 8192 | false | false | false | true |
| `per_layer_embeddings` | 1.367 | 1.283 | 1.338 | 8192 | false | false | false | true |

## Evidence Notes
- Training matrix coverage: seq_lens `[8, 16]`, steps `[4]`, seeds `[17]`.
- Training evidence coverage: `attention_budgeting`, `compressed_attention`, `history_compression`, `kv_sharing`, `mhc`, `per_layer_embeddings`
- Matrix winners: fastest `per_layer_embeddings`, lowest final-loss delta `compressed_attention`, lowest grad-delta `attention_budgeting`.
- Stable matrix leaders: speed `per_layer_embeddings`, loss `compressed_attention`.
- Matrix winner counts: `{"fastest_step_ratio": {"attention_budgeting": 1, "per_layer_embeddings": 1}, "lowest_final_loss_delta": {"compressed_attention": 2}, "lowest_grad_norm_delta": {"attention_budgeting": 1, "kv_sharing": 1}}`
- Focused review priorities: `kv_sharing`
- Raw audit mismatches: `attention_budgeting`
- Resolved mismatches via focused follow-up: `attention_budgeting`
- Benchmark matrix coverage: batch sizes `[1, 2]`, seq_lens `[4, 8, 16]`, grid cells `6`.
- Benchmark matrix leaders: mean runtime `compressed_attention`, worst-case runtime tie between `attention_budgeting`, `compressed_attention`, lowest KV tie between `compressed_attention`, `kv_sharing`.
- Focused long-context proxy compare summary: `{"selected_bucket": {"variant_kind": "compressed_attention", "filler_repeats": 256, "num_cases": 4, "mean_proxy_pass_probability": 0.9551999999999999, "proxy_pass_rate": 1.0, "min_proxy_pass_probability": 0.9551999999999999, "max_proxy_pass_probability": 0.9551999999999999, "estimated_kv_cache_bytes_at_max_seq": 2348810240, "estimated_kv_saving_ratio_at_max_seq": 0.0, "estimated_total_params": 507961344}, "baseline_bucket": {"variant_kind": "baseline", "filler_repeats": 256, "num_cases": 4, "mean_proxy_pass_probability": 0.995, "proxy_pass_rate": 1.0, "min_proxy_pass_probability": 0.995, "max_proxy_pass_probability": 0.995, "estimated_kv_cache_bytes_at_max_seq": 4697620480, "estimated_kv_saving_ratio_at_max_seq": 0.0, "estimated_total_params": 596041728}, "proxy_quality_delta": -0.03980000000000006, "proxy_kv_bytes_delta": -2348810240}`
