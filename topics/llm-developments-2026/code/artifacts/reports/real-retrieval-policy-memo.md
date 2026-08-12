# Real Retrieval Policy Memo

Recommended retrieval default: `real_retrieval_lexical`

## Retrieval Candidates

| Policy | Accepted | Grounded | Gold-Hit Tasks | Mean Gold Recall | Validation | Mean Context Snippets | Tokens / Accepted Task |
|---|---:|---:|---:|---:|---:|---:|---:|
| `real_retrieval_lexical` | 0.933 | 1.000 | 0.933 | 0.628 | 1.000 | 2.0 | 406.8 |
| `real_retrieval_sparse` | 0.867 | 1.000 | 0.867 | 0.528 | 1.000 | 1.9 | 407.8 |
| `real_retrieval_task_aware` | 0.733 | 1.000 | 0.733 | 0.578 | 1.000 | 2.0 | 412.5 |

## Why
- It matches or exceeds the baseline retrieval policies on accepted and grounded rates.

## Acceptance Swings Vs Lexical
- No task changed acceptance between lexical retrieval and the recommended policy.

## Common Misses
- `architecture-advances-2026/code/src/arch_adv_2026/compressed_attention_promotion_assessment.py` missed on 2 task(s) by the recommended policy.
- `architecture-advances-2026/code/src/arch_adv_2026/long_context_eval.py` missed on 2 task(s) by the recommended policy.
- `llm-developments-2026/code/artifacts/reports/real-retrieval-policy-memo.md` missed on 2 task(s) by the recommended policy.
- `llm-developments-2026/code/src/llm_dev_2026/verifier.py` missed on 2 task(s) by the recommended policy.
- `architecture-advances-2026/docs/attention-budgeting.md` missed on 1 task(s) by the recommended policy.

## Notes
- This memo compares only retrieval-backed policies against each other.
- It does not treat the gold-evidence baseline as a fair replacement target because gold context is an oracle, not a runtime retrieval policy.
