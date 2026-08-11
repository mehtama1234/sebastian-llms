# Focused Long-Context Follow-up Assessment

_Updated: 2026-08-09_

## Conclusion
- Focused long-context follow-up for `kv_sharing` supports the candidate `secondary` label over the current `exploratory` label.

## Signals
- variant saves KV cache at the longest context
- variant reduces longest-context KV bytes versus baseline
- quality stays close to baseline while KV cost drops materially

## Longest-Context Comparison

| Variant | Proxy Quality | Proxy Pass Rate | KV Bytes | KV Saving Ratio |
|---|---:|---:|---:|---:|
| `baseline` | 0.995 | 1.000 | 4697620480 | 0.000 |
| `kv_sharing` | 0.975 | 1.000 | 2348810240 | 0.500 |
