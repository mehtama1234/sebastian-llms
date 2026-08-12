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

## Real benchmark update

On Wednesday, August 12, 2026, the real-task benchmark lane produced a separate retrieval-default recommendation for the runtime path:

- **Recommended real retrieval default:** `real_retrieval_lexical`
- On the widened 15-task sample real benchmark, lexical retrieval reached the strongest accepted rate (`0.933`) while sparse landed at `0.867` and task-aware at `0.733`.
- All retrieval-backed candidates remained fully grounded and fully validation-clean on the sample.
- Lexical also led on mean gold-file recall (`0.628` vs `0.528` sparse and `0.578` task-aware).
- Tokens per accepted task stayed close (`406.8` lexical, `407.8` sparse, `412.5` task-aware), so the acceptance gap now matters more than the cost gap.
- The new slice report adds the useful nuance:
  `lexical` is best on the 5-task `inspect` slice and on the short-context slice, `task_aware` is best on the enlarged 5-task `diagnose` slice, and `sparse` remains the best long-context and research default.

This does not replace the synthetic memo above. It answers a different question:

- the synthetic memo chooses defaults for the deterministic harness sweep
- the real retrieval memo chooses the best retrieval-backed runtime policy among real benchmark candidates
- the slice report shows where that pooled default is strongest or weakest by task type

See `../code/artifacts/reports/real-retrieval-policy-memo.md` and `../code/artifacts/reports/real-retrieval-slice-report.md` for the retrieval-specific artifacts.
