# Focused Training Follow-up Assessment

_Updated: 2026-08-09_

## Conclusion
- Focused training follow-up for `kv_sharing` supports the candidate `exploratory` label over the current `secondary` label.

## Signals
- mean final-loss delta is worse than baseline
- loss advantage is not consistent across the follow-up grid
- speed advantage is not consistent across the follow-up grid
- all follow-up rows stayed finite
- the follow-up is weak enough on loss or speed to support a more conservative label

## Trend Row

| Variant | Mean Loss Delta | Loss Range | Mean Speed Ratio | Speed Range | Consistent Loss | Consistent Speed |
|---|---:|---:|---:|---:|---:|---:|
| `kv_sharing` | 1.400 | 5.091 | 0.703 | 0.642 | false | false |
