# Compressed Attention Training Stress Assessment

_Updated: 2026-08-09_

## Conclusion
- Focused compressed_attention stress follow-up does not strongly reproduce the diagnosed weakness.

## Signals
- Mean loss delta: `0.000`
- Mean speed ratio: `1.000`
- Positive-loss row fraction: `0.000`
- Slow-row fraction: `0.000`
- the stress grid does not clearly reproduce a broad loss failure
- the stress grid does not show a broad speed-tail problem

## Stress Coverage
- Batch sizes: `[2, 4]`
- Seq lens: `[8]`
- Steps: `[4, 8]`
- Seeds: `[23, 29, 31]`
- Report runs: `2`

## Worst Rows

| Kind | Batch | Seq Len | Steps | Seed | Loss Delta | Speed Ratio |
|---|---:|---:|---:|---:|---:|---:|
| `worst_loss` | 2 | 8 | 4 | 23 | 0.000 | 1.000 |
| `slowest` | 2 | 8 | 4 | 23 | 0.000 | 1.000 |
