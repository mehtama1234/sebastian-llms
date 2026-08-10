# Compressed Attention Promotion Goal

This is the next meaty end-to-end goal for `architecture-advances-2026`.

The current stack already answers the first question: which concept looks best on the present micro, proxy, and focused follow-up evidence?

As of August 9, 2026, that answer is `compressed_attention`.

The next question is harder and more valuable:

Can `compressed_attention` graduate from "current carry-forward winner" to "default architecture for the next heavier experiment stage"?

## Goal

Build one promotion-grade evidence pass for `compressed_attention` that is strong enough to support a real architecture decision instead of a provisional proxy win.

The end state is not another isolated benchmark.

The end state is a refreshed decision stack that can say:

- `compressed_attention` is ready for the next heavier model or training stage
- or `compressed_attention` still needs more evidence before promotion

## Why this is the right next milestone

The current memo already says:

- `compressed_attention` is the default carry-forward architecture
- it is the strongest blended quality-preserving systems trade
- it still needs a wider training schedule check before we treat the decision as fully closed

That means the highest-value next step is not another narrow argument about every variant.

It is to strengthen the evidence around the current winner until the recommendation becomes promotion-grade.

## Concrete deliverables

The repo should gain one integrated evaluation lane for `compressed_attention` covering three surfaces.

### 1. Harder long-context evaluation

Expand beyond the current proxy selector and focused rerun.

Deliverables:

- a broader long-context case set with harder retrieval and degradation cases
- a named execution artifact for `compressed_attention` on that harder set
- a comparison artifact against baseline with explicit quality deltas and pass rates

Exit criteria:

- `compressed_attention` keeps acceptable retrieval quality on harder cases
- the quality loss is small enough to justify the memory/runtime trade

### 2. Broader training matrix

Expand the current tiny training matrix so the observed loss win is not resting on one narrow schedule.

Deliverables:

- more than one seed
- more than one step count
- more than one sequence-length setting
- a `compressed_attention`-specific follow-up artifact and assessment

Exit criteria:

- the loss advantage stays directionally positive across the wider grid
- instability is bounded and visible rather than hidden by a single row

### 3. Wider systems sweep

Confirm that the current systems advantage is not an artifact of the present micro grid.

Deliverables:

- a broader benchmark matrix with more batch-size and sequence-length cells
- updated mean, median, and worst-cell summaries for `compressed_attention`
- an explicit comparison against `kv_sharing` on the same widened grid

Exit criteria:

- `compressed_attention` remains near baseline or better on blended runtime
- worst-case regressions stay within a tolerable bound for a default candidate

## Decision question

At the end of this milestone, the memo should answer one concrete question:

Should `compressed_attention` become the default architecture for the next heavier experiment stage, with `kv_sharing` kept only as a special-case memory branch?

That is the promotion decision.

## What changes in the repo

This milestone should produce:

- new scripts or script flags for broader `compressed_attention` follow-ups
- refreshed artifacts under `artifacts/reports/` and `artifacts/long_context/`
- an updated final memo, scorecard, audit, and review plan
- a short decision note explaining whether promotion is now justified

## Suggested execution order

1. Add the broader `compressed_attention` training follow-up path.
2. Add the harder long-context execution lane for `compressed_attention`.
3. Widen the benchmark matrix for the same variant and baseline.
4. Rebuild the full decision stack.
5. Write the promotion decision note.

## Done means

Done means we have enough evidence to either promote or explicitly defer `compressed_attention`.

It does not mean the result has to be positive.

It means the repo can support a defensible answer to the next-stage architecture question with refreshed, heavier evidence instead of only the current micro and proxy surfaces.
