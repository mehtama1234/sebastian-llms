# Mechanism proxy report

Run date: 2026-11-25  
Evidence level: executable toy proxy  
Status: `PASSED`

This report intentionally models accounting boundaries, not a released model.
All reported numbers come from `frontier_mechanisms.py` and its tests. The
current focused mechanism/config regression run is `18 passed`; it also checks
that compressed positions remain causally invisible until their group closes.

## Cache ownership and selection

The storage formula is:

```text
bytes/token/owner = 2 × KV_heads × head_dim × bytes/element
stored bytes = owner layers × sequence length × bytes/token/owner
```

For 32 layers, 8 KV heads, head dimension 128, BF16, and 131,072 tokens:

```text
2 × 8 × 128 × 2 = 4,096 bytes/token/owner
32 × 131,072 × 4,096 = 17,179,869,184 bytes = 16 GiB
```

Sharing every two layers halves stored cache bytes to 8 GiB in this toy. It does
not automatically halve cache reads: both fresh-selection and reused-selection
variants still read selected entries for all consumer layers. Reused selection
halves the synthetic index-query count from 32 layers to 16 owner groups.

## Changing-query distractor probe

The 12-token fixture contains two distant targets and lower-scoring distractors.
Query 0 favors target index 2; query 1 favors target index 5.

| Policy | Target hits | Index work | Interpretation |
|---|---:|---:|---|
| Fresh selection | 2/2 | 24 units | Recomputes selection for each query. |
| Reused selection | 1/2 | 12 units | Saves index work but retains stale indices for the changed query. |

The result supports a narrow claim: selection reuse is a compute/storage tradeoff,
not a free quality improvement. It does not estimate real retrieval accuracy.

## Recurrent state plus periodic lookup

The recurrent proxy stores a fixed state:

```text
fixed state bytes = layers × state width × bytes/element
```

Lookup events scale as `ceil(sequence length / lookup period)`. This separates
state capacity from explicit token-addressable history. A fixed recurrent state
can be cheap at long context while still needing periodic lookup for exact,
distant recall.

## Shared-weight depth

For 24 stored layers, looping the middle 12 layers three times gives:

```text
(24 − 12) + (12 × 3) = 48 layer applications/token
```

The stored weight depth remains 24. This is additional internal computation
with reused weights, not a claim of lower KV state or extra visible reasoning
tokens.

## Limits and next experiment

The proxy uses synthetic scores, no learned indexer, no real paging, no device
timings, and no task-quality model. The next conclusion-changing experiment is
to run the same accounting and selection matrix over fixed distractor prompts
with an approved local checkpoint/runtime, logging exact recall, state handoff,
bytes touched, and first-token/decode latency separately.
