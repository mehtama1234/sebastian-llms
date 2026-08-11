# Adoption Memo — llm-developments-2026-default

Baseline honest success: **67%**

## Axis decisions

### retrieval
- **Recommended:** `baseline`
- lexical/grep already solves 67% of tasks; vector and hybrid did not raise honest success, so keep lexical as the default and reserve vector for known paraphrase-heavy corpora.

### context
- **Recommended:** `baseline`
- baseline holds success at 67% while spending 62 prompt tokens vs 62 for full inlining; cheaper policies that dropped evidence were rejected on success.

### instructions
- **Recommended:** `instructions_hierarchical`
- instructions_hierarchical reaches 83% honest success; guidance-dependent tasks are unsolvable without the matching instruction file, at a per-task cost of +35 tokens.

### verifier
- **Recommended:** `verifier_on`
- the verifier cut hallucinated success from 17% to 0% by escalating ungrounded claims instead of shipping them; reported success drops but honest success is unchanged or higher.

### test_time_scaling
- **Recommended:** `attempts_multi`
- attempts_multi raised honest success to 75% (from 67%) on flaky-recall tasks, at 1.6 mean attempts vs 1.0.

## Combined production candidate vs baseline
- honest success: +0.33
- hallucination: -0.17
- latency units: +578

> Numbers come from a deterministic synthetic benchmark. They test harness
> *policy* tradeoffs and their direction, not absolute production quality.
