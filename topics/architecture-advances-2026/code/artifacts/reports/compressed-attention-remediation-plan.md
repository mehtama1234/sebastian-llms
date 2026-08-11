# Compressed Attention Remediation Plan

_Updated: 2026-08-09_

## Current State
- Promotion recommendation: `defer`
- Gates: long-context `true`, training `false`, systems `false`

## Next Steps
- P1: Stabilize short-context training loss
  Why: The focused stress rerun on August 9, 2026 reproduced worse-than-baseline loss on the short-context slice.
  Target: `{"batch_size": 2, "seed": 23, "seq_len": 8, "steps": 4}`
  Success: mean final-loss delta on the stressed short-context slice moves to 0 or below
  Success: positive-loss row fraction drops below 0.5 on the focused stress grid
- P2: Reduce broad short-context slowdown at the small batch slice
  Why: Batch 2 has the broadest slow-row concentration in the current short-context speed-tail assessment.
  Target: `{"batch_size": 2, "seq_len": 8, "steps": 4}`
  Success: slow-row fraction on the broad slowdown slice drops below 0.5
  Success: mean speed ratio on that slice moves to 1.0 or below
- P3: Eliminate the worst speed-tail event
  Why: Batch 2 contains the current worst short-context speed ratio, with the worst tail concentrated at 4 steps.
  Target: `{"batch_size": 2, "seed": 23, "seq_len": 8, "steps": 4}`
  Success: worst speed ratio on the focused stress grid drops below 1.2
  Success: no single stressed row shows an outsized tail event relative to the rest of the grid
- P4: Reconfirm worst-case systems stability after the training fix
  Why: The current promotion assessment still marks the systems gate as failed on the broader grid.
  Target: `{"batch_sizes": [1, 2, 4], "seq_lens": [4, 8, 16, 32]}`
  Success: worst runtime ratio in the promotion benchmark matrix drops to 1.10 or below
