# Indexer vs Attention Goal

This is the next meaty end-to-end goal for the long-context side of `architecture-advances-2026`.

The current architecture lane already has:

- compressed-attention prototypes
- long-context proxy evaluation
- decision-stack scripts
- a carry-forward winner in `compressed_attention`

What it does **not** yet have is a clean, first-class answer to the deeper question behind the DeepSeek discussion:

**when can a sparse selector or indexer safely replace broader attention-style context access, and when does it miss something essential?**

That is a different question from:

- whether compressed attention helps
- whether KV sharing helps
- whether a smaller proxy benchmark likes a given variant

It is the explicit **indexer vs attention** question.

## Goal

Build one controlled experiment lane where a sparse indexer competes directly against fuller attention-style context access on the same long-context tasks, with explicit quality and systems tradeoffs.

The end state is not:

- another note about DeepSeek
- another proxy retrieval heuristic
- another isolated benchmark artifact

The end state is:

- one repeatable comparison harness
- one set of indexer variants
- one set of fuller-context baselines
- one metric bundle for recall, quality, and cost
- one decision memo saying when the selector is trustworthy and when it is not

## The concrete question

For long-context tasks, we want to answer:

1. How much quality can we keep if we let an indexer choose what the model looks at?
2. How fast does quality degrade as the selected budget shrinks?
3. Which failures come from bad selection versus bad reasoning after selection?
4. When is a sparse selector good enough to replace broader attention access?
5. When should we keep fuller attention because recall loss is too dangerous?

## What we are building

We want one place in the repo where we can compare:

- broader context access baselines
- local-window plus global-anchor baselines
- sparse selector plus rerank variants
- compressed historical access variants

on the **same** long-context tasks.

The indexer side should be treated as a first-class architecture surface, not as an accidental byproduct of retrieval plumbing.

## Minimum comparison set

The first useful comparison matrix should contain at least these variants:

1. `fuller_context_baseline`
   - bigger context slice or dense-ish access
   - reference for quality

2. `window_plus_anchor`
   - local recent tokens plus a fixed set of global anchors
   - cheap structured baseline

3. `sparse_indexer_lexical`
   - cheap selector over long history
   - exact rerank on shortlist

4. `sparse_indexer_mixed`
   - selector uses both path/content overlap style signals
   - exact rerank on shortlist

5. `compressed_attention_reference`
   - current carry-forward architecture lane winner
   - acts as the systems-aware comparison point

## Required metrics

This lane is only useful if it measures more than end-task success.

It must report:

- support-file recall
- support-span recall
- top-k hit rate
- answer correctness
- degradation under distractors
- degradation as selection budget shrinks
- prompt or context budget used
- latency proxy
- worst-case miss examples

The key idea is:

**selection quality must be measured directly, not only inferred from final success.**

## Required task types

The benchmark slice must contain tasks where selection really matters:

- one-fact-far-away tasks
- multi-hop evidence spread across distant chunks
- distractor-heavy contexts
- long technical explanation tasks
- code-path tracing across multiple files

If the tasks are too easy, full attention and sparse selection will both look fine and the lane will tell us nothing.

## Implementation target

The repo should gain one focused experiment path with these pieces:

### 1. Long-context case pack

Add a case pack with explicit:

- gold files
- gold spans
- distractor files
- context budget classes
- difficulty buckets

### 2. Selector variants

Add selector modules or configs that can:

- rank candidate chunks
- return a shortlist
- vary budget `k`
- record which chunks were chosen

### 3. Baseline attention-style access

Add baselines that simulate or implement:

- broader dense access
- structured window plus anchors

so the selector is always judged against something concrete.

### 4. Diagnostics and reports

Add artifacts that show:

- what was selected
- what should have been selected
- whether the miss was recoverable
- how the failure changed the final answer

## First milestone

The first milestone is reached when the repo can:

- run one long-context task pack with at least 20 tasks
- compare at least 4 selector/access variants
- sweep more than one selection budget
- produce one report showing:
  - recall curves
  - answer-quality curves
  - latency or cost curves
  - concrete miss cases

At that point the lane stops being a conceptual extension of retrieval and becomes a real indexer-vs-attention experiment.

## Decision question

At the end of the milestone, the memo should answer:

**Should we trust sparse selection as a default long-context access strategy for the next heavier architecture stage, or only as a limited efficiency branch?**

That is the real decision.

## Suggested execution order

1. Add the long-context case pack with gold spans and distractors.
2. Add explicit selector variants and budget sweeps.
3. Add broader-access baselines for comparison.
4. Add recall and miss diagnostics.
5. Run the comparison matrix.
6. Write the decision memo.

## Done means

Done does not mean the sparse selector wins.

Done means the repo can support a defensible answer to:

- when the indexer is good enough
- when the indexer is unsafe
- how much budget is enough
- whether broader attention access is still worth paying for

That is the meaty next end state for this direction.
