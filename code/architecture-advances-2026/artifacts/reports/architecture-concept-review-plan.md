# Architecture Concept Review Plan

_Updated: 2026-08-09_

## Summary
- Priority variants: `kv_sharing`
- Raw decision mismatches from the audit: `attention_budgeting`
- Resolved mismatches with follow-up support for the current label: `attention_budgeting`
- Review rows: `6`

## Review Queue
- `kv_sharing`: current `secondary`, suggested `secondary`, priority `2`.
  - Focused follow-up evidence is mixed for `kv_sharing`, but the stronger weighted signal still favors keeping `secondary` over `exploratory`.
  - Run a broader training matrix for `kv_sharing` because the current training-loss signal is weak or unstable.
  - Profile `kv_sharing` under a wider training schedule grid because the current training speed signal is not a stable advantage.
  - Recheck `kv_sharing` on a broader systems sweep because its worst micro benchmark cell regresses above 1.2x baseline.
- `attention_budgeting`: current `drop`, suggested `drop`, priority `1`.
  - Focused follow-up evidence already supports keeping `attention_budgeting` at `drop`; resolve the mismatch by updating thresholds or gathering non-training evidence.
  - Do not treat `attention_budgeting` as a memory-saving path until a different surface shows a compensating quality gain.
- `history_compression`: current `exploratory`, suggested `exploratory`, priority `1`.
  - Expand long-context evaluation for `history_compression` with more hard retrieval cases because current longest-context proxy quality is below the strong keep bar.
  - Profile `history_compression` under a wider training schedule grid because the current training speed signal is not a stable advantage.
- `mhc`: current `exploratory`, suggested `exploratory`, priority `1`.
  - Profile `mhc` under a wider training schedule grid because the current training speed signal is not a stable advantage.
  - Recheck `mhc` on a broader systems sweep because its worst micro benchmark cell regresses above 1.2x baseline.
  - Treat `mhc` as systems-expensive for now and require a stronger quality win before promotion.
  - Do not treat `mhc` as a memory-saving path until a different surface shows a compensating quality gain.
- `compressed_attention`: current `default`, suggested `default`, priority `0`.
  - Profile `compressed_attention` under a wider training schedule grid because the current training speed signal is not a stable advantage.
- `per_layer_embeddings`: current `drop`, suggested `drop`, priority `0`.
  - Run a broader training matrix for `per_layer_embeddings` because the current training-loss signal is weak or unstable.
  - Recheck `per_layer_embeddings` on a broader systems sweep because its worst micro benchmark cell regresses above 1.2x baseline.
  - Treat `per_layer_embeddings` as systems-expensive for now and require a stronger quality win before promotion.
  - Do not treat `per_layer_embeddings` as a memory-saving path until a different surface shows a compensating quality gain.

## Notes
- This review plan converts scorecard and audit findings into concrete next experiments or hold decisions.
- Higher priority means either an explicit unresolved decision mismatch or a current keep-label with unresolved evidence gaps.
