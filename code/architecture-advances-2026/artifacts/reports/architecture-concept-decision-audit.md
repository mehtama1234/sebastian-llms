# Architecture Concept Decision Audit

_Updated: 2026-08-09_

## Summary
- Variants audited: `6`
- Decision mismatches: `1`
- Mismatch variants: `attention_budgeting`
- Mismatches resolved by focused follow-up: `attention_budgeting`

## Decision Matrix

| Variant | Current | Suggested | Match | Follow-up Resolved | Why |
|---|---|---|---:|---:|---|
| `compressed_attention` | default | default | true | false | strong blended winner: clears long-context, near-parity systems-sweep, and training-loss gates |
| `kv_sharing` | secondary | secondary | true | false | keep candidate: clears long-context bar and enough systems/training support for a bounded keep |
| `history_compression` | exploratory | exploratory | true | false | promising but incomplete: some quality/training support without enough stable systems evidence |
| `mhc` | exploratory | exploratory | true | false | promising but incomplete: some quality/training support without enough stable systems evidence |
| `attention_budgeting` | drop | secondary | false | true | keep candidate: clears long-context bar and enough systems/training support for a bounded keep |
| `per_layer_embeddings` | drop | drop | true | false | insufficient blended evidence for carry-forward |

## Notes
- This audit applies explicit decision rules to the concept scorecard and compares the result to the current memo labels.
- A mismatch is not automatically a bug; it marks where the current narrative and the current thresholds disagree.
- Focused follow-up evidence can mark a raw mismatch as resolved even when the base threshold rule still points elsewhere.
