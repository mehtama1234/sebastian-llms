# Long-context variant proxy decision memo

## Bottom line
- Best longest-context proxy quality: `mhc` (0.999).
- Best longest-context KV savings inside the quality bar: `compressed_attention` (2348810240 bytes, saving ratio 0.000).
- Best overall carry-forward candidate from this proxy selector: `compressed_attention`.
- Quality threshold used for memory-preserving picks: `0.950`.

## Recommendations
- Carry forward `compressed_attention` as the default long-context efficiency candidate for the next heavier experiment tier.
- Keep `mhc` as the quality ceiling reference for proxy long-context behavior.
- Keep `compressed_attention` as the aggressive memory-reduction candidate when KV footprint dominates the requirement.
- The selector did not need fallback, so the memory-oriented recommendation already clears the requested proxy-quality threshold.

## Selector Picks

| Objective | Variant | Proxy Quality | Proxy Pass Rate | KV Bytes | KV Saving Ratio | Total Params |
|---|---|---:|---:|---:|---:|---:|
| `quality` | `mhc` | 0.999 | 1.000 | 4697620480 | 0.000 | 629157888 |
| `memory` | `compressed_attention` | 0.955 | 1.000 | 2348810240 | 0.000 | 507961344 |
| `quality_preserving_memory` | `compressed_attention` | 0.955 | 1.000 | 2348810240 | 0.000 | 507961344 |
| `balanced` | `compressed_attention` | 0.955 | 1.000 | 2348810240 | 0.000 | 507961344 |

## Policy
- Longest filler bucket: `256`
- Minimum proxy quality: `0.950`
- Acceptable rows: `6` / `7`
- Used fallback rows: `False`

## Report Context
- Variant count in report: `6`
- Cases per length: `2`
- Sweep runs: `2`
