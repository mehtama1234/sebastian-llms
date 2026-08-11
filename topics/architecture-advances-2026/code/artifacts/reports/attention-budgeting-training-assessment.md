# Focused Training Follow-up Assessment

_Updated: 2026-08-09_

## Conclusion
- Focused training follow-up for `attention_budgeting` supports the current `drop` label over the candidate `secondary` label.

## Signals
- mean final-loss delta is worse than baseline
- mean training step time is slower than baseline
- loss advantage is not consistent across the follow-up grid
- speed advantage is not consistent across the follow-up grid
- all follow-up rows stayed finite

## Trend Row

| Variant | Mean Loss Delta | Loss Range | Mean Speed Ratio | Speed Range | Consistent Loss | Consistent Speed |
|---|---:|---:|---:|---:|---:|---:|
| `attention_budgeting` | 0.439 | 6.880 | 1.099 | 1.253 | false | false |
