# Compressed Attention Promotion Assessment

_Updated: 2026-08-09_

## Recommendation
- Recommendation: `defer`
- Compressed attention should remain the default carry-forward candidate, but promotion should be deferred until the weaker evidence surfaces are widened or improved.

## Gate Status
- Long-context gate: `true`
- Training gate: `false`
- Systems gate: `false`

## Positive Signals
- hardest available long-context proxy bucket stays at full pass rate with acceptable quality loss
- long-context execution still saves KV cache relative to baseline

## Risks
- training follow-up does not yet show a consistent loss advantage across the sampled grid
- training speed advantage is not consistent across the follow-up grid
- systems sweep still shows too much runtime regression for a default promotion

## Evidence Snapshot

| Surface | Key Metrics |
|---|---|
| Long-context | quality delta `-0.020`; pass-rate delta `0.000`; KV saving `0.250` |
| Training | mean loss delta `-0.696`; loss range `4.802`; mean speed ratio `1.059`; consistent loss `false` |
| Systems | mean runtime ratio `0.981`; worst runtime ratio `1.105`; KV bytes `4096` |
