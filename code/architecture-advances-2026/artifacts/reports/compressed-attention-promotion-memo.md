# Compressed attention promotion memo

_Updated: 2026-08-09_

## Bottom line
- Promotion recommendation: `defer` for `compressed_attention`.
- Gate state: long-context `true`, training `false`, systems `false`.
- Long-context proxy quality delta vs baseline: `-0.020` with KV saving ratio `0.250`.
- Training mean loss delta vs baseline: `-0.696` with range `4.802`.
- Systems mean runtime ratio: `0.981`; worst runtime ratio: `1.105`.
- Focused stress follow-up reproduces failure: `false`; slow-tail persists: `false`.
- Short-context speed tail: broadest slow-row concentration at batch `2` (slow fraction `0.000`), but worst tail at batch `2` with worst speed ratio `1.000` and step slice `4`.

## Recommendations
- Keep `compressed_attention` as the default carry-forward candidate rather than promoting it yet.
- Treat the failed gates as the next concrete work queue instead of reopening the whole architecture search.
- Prioritize a broader training schedule follow-up because training evidence is still the limiting surface.
- Recheck worst-case systems behavior on an even broader grid before promotion.
- Treat batch `2` as the broad slowdown slice and `4` steps as the worst tail slice in the next training investigation.

## Positive Signals
- hardest available long-context proxy bucket stays at full pass rate with acceptable quality loss
- long-context execution still saves KV cache relative to baseline

## Risks
- training follow-up does not yet show a consistent loss advantage across the sampled grid
- training speed advantage is not consistent across the follow-up grid
- systems sweep still shows too much runtime regression for a default promotion
