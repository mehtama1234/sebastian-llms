# Compressed Attention Candidate Probe

## Summary

| Candidate | Mean Loss Delta | Max Loss Delta | Mean Train Speed | Max Train Speed | Mean Bench Ratio | Worst Bench Ratio |
|---|---:|---:|---:|---:|---:|---:|
| `micro-compressed-attention-t24` | 0.000 | 0.000 | 1.000 | 1.000 | 0.967 | 1.000 |
| `micro-compressed-attention-d13t24` | 0.000 | 0.000 | 1.000 | 1.000 | 0.995 | 1.065 |
| `micro-compressed-attention-d12` | -2.142 | 0.216 | 1.075 | 1.395 | 1.016 | 1.137 |
| `micro-compressed-attention-d12q6` | -2.063 | 0.852 | 1.088 | 1.536 | 1.103 | 1.223 |
| `micro-compressed-attention-d14` | -0.343 | 3.187 | 1.098 | 1.430 | 1.005 | 1.200 |
| `micro-compressed-attention-current` | 0.112 | 3.561 | 0.958 | 1.568 | 0.884 | 1.002 |

## Selection Heuristic
- Candidates are sorted by max loss delta first, then worst benchmark ratio, then mean loss delta, then mean benchmark ratio.

## Probe Grids
- Training: batch sizes `[2, 4]`, seq lens `[16]`, steps `[4, 8]`, seeds `[17, 23]`, report runs `2`.
- Benchmark: batch sizes `[1, 2, 4]`, seq lens `[16, 32]`, warmup `1`, measured `3`, report runs `3`.
