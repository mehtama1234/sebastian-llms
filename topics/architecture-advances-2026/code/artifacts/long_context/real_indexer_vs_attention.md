# Real Indexer vs Attention Report

## Summary

| Variant | Mean Support Recall | Any Hit Rate | Exact Hit Rate | Mean Prompt Tokens | Budgets |
|---|---:|---:|---:|---:|---|
| `lexical_retrieval_order` | 0.500 | 0.667 | 0.333 | 389.3 | 1, 2, 3 |
| `sparse_retrieval_order` | 0.458 | 0.583 | 0.333 | 387.9 | 1, 2, 3 |
| `anchor_then_tail` | 0.167 | 0.167 | 0.167 | 374.5 | 1, 2, 3 |
| `union_lexical_rerank` | 0.417 | 0.417 | 0.417 | 392.8 | 1, 2, 3 |
| `union_structured_rerank` | 0.458 | 0.500 | 0.417 | 285.3 | 1, 2, 3 |
| `task_aware_balanced_rerank` | 0.833 | 1.000 | 0.667 | 286.2 | 1, 2, 3 |

## Rows

| Task | Variant | Budget | Recall | Any Hit | Exact Hit | Prompt Tokens |
|---|---|---:|---:|---:|---:|---:|
| `topics.inspect.deepseek_architecture_lane` | `lexical_retrieval_order` | 1 | 0.000 | false | false | 229 |
| `topics.inspect.deepseek_architecture_lane` | `lexical_retrieval_order` | 2 | 0.000 | false | false | 414 |
| `topics.inspect.deepseek_architecture_lane` | `lexical_retrieval_order` | 3 | 0.500 | true | false | 617 |
| `topics.inspect.deepseek_architecture_lane` | `sparse_retrieval_order` | 1 | 0.000 | false | false | 229 |
| `topics.inspect.deepseek_architecture_lane` | `sparse_retrieval_order` | 2 | 0.000 | false | false | 414 |
| `topics.inspect.deepseek_architecture_lane` | `sparse_retrieval_order` | 3 | 0.500 | true | false | 617 |
| `topics.inspect.deepseek_architecture_lane` | `anchor_then_tail` | 1 | 0.000 | false | false | 163 |
| `topics.inspect.deepseek_architecture_lane` | `anchor_then_tail` | 2 | 0.000 | false | false | 392 |
| `topics.inspect.deepseek_architecture_lane` | `anchor_then_tail` | 3 | 0.000 | false | false | 578 |
| `topics.inspect.deepseek_architecture_lane` | `union_lexical_rerank` | 1 | 0.000 | false | false | 229 |
| `topics.inspect.deepseek_architecture_lane` | `union_lexical_rerank` | 2 | 0.000 | false | false | 414 |
| `topics.inspect.deepseek_architecture_lane` | `union_lexical_rerank` | 3 | 0.000 | false | false | 554 |
| `topics.inspect.deepseek_architecture_lane` | `union_structured_rerank` | 1 | 0.000 | false | false | 229 |
| `topics.inspect.deepseek_architecture_lane` | `union_structured_rerank` | 2 | 0.000 | false | false | 369 |
| `topics.inspect.deepseek_architecture_lane` | `union_structured_rerank` | 3 | 0.000 | false | false | 554 |
| `topics.inspect.deepseek_architecture_lane` | `task_aware_balanced_rerank` | 1 | 0.500 | true | false | 108 |
| `topics.inspect.deepseek_architecture_lane` | `task_aware_balanced_rerank` | 2 | 1.000 | true | true | 311 |
| `topics.inspect.deepseek_architecture_lane` | `task_aware_balanced_rerank` | 3 | 1.000 | true | true | 540 |
| `topics.diagnose.llm_dev_verifier_flow` | `lexical_retrieval_order` | 1 | 0.500 | true | false | 169 |
| `topics.diagnose.llm_dev_verifier_flow` | `lexical_retrieval_order` | 2 | 0.500 | true | false | 550 |
| `topics.diagnose.llm_dev_verifier_flow` | `lexical_retrieval_order` | 3 | 0.500 | true | false | 631 |
| `topics.diagnose.llm_dev_verifier_flow` | `sparse_retrieval_order` | 1 | 0.000 | false | false | 381 |
| `topics.diagnose.llm_dev_verifier_flow` | `sparse_retrieval_order` | 2 | 0.500 | true | false | 550 |
| `topics.diagnose.llm_dev_verifier_flow` | `sparse_retrieval_order` | 3 | 0.500 | true | false | 631 |
| `topics.diagnose.llm_dev_verifier_flow` | `anchor_then_tail` | 1 | 0.000 | false | false | 381 |
| `topics.diagnose.llm_dev_verifier_flow` | `anchor_then_tail` | 2 | 0.000 | false | false | 519 |
| `topics.diagnose.llm_dev_verifier_flow` | `anchor_then_tail` | 3 | 0.000 | false | false | 643 |
| `topics.diagnose.llm_dev_verifier_flow` | `union_lexical_rerank` | 1 | 0.000 | false | false | 381 |
| `topics.diagnose.llm_dev_verifier_flow` | `union_lexical_rerank` | 2 | 0.000 | false | false | 493 |
| `topics.diagnose.llm_dev_verifier_flow` | `union_lexical_rerank` | 3 | 0.000 | false | false | 574 |
| `topics.diagnose.llm_dev_verifier_flow` | `union_structured_rerank` | 1 | 0.000 | false | false | 81 |
| `topics.diagnose.llm_dev_verifier_flow` | `union_structured_rerank` | 2 | 0.000 | false | false | 193 |
| `topics.diagnose.llm_dev_verifier_flow` | `union_structured_rerank` | 3 | 0.500 | true | false | 302 |
| `topics.diagnose.llm_dev_verifier_flow` | `task_aware_balanced_rerank` | 1 | 0.500 | true | false | 109 |
| `topics.diagnose.llm_dev_verifier_flow` | `task_aware_balanced_rerank` | 2 | 0.500 | true | false | 278 |
| `topics.diagnose.llm_dev_verifier_flow` | `task_aware_balanced_rerank` | 3 | 0.500 | true | false | 390 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `lexical_retrieval_order` | 1 | 0.000 | false | false | 86 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `lexical_retrieval_order` | 2 | 0.000 | false | false | 167 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `lexical_retrieval_order` | 3 | 1.000 | true | true | 255 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `sparse_retrieval_order` | 1 | 0.000 | false | false | 86 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `sparse_retrieval_order` | 2 | 0.000 | false | false | 167 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `sparse_retrieval_order` | 3 | 1.000 | true | true | 255 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `anchor_then_tail` | 1 | 0.000 | false | false | 104 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `anchor_then_tail` | 2 | 1.000 | true | true | 192 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `anchor_then_tail` | 3 | 1.000 | true | true | 273 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `union_lexical_rerank` | 1 | 0.000 | false | false | 86 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `union_lexical_rerank` | 2 | 1.000 | true | true | 174 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `union_lexical_rerank` | 3 | 1.000 | true | true | 255 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `union_structured_rerank` | 1 | 0.000 | false | false | 86 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `union_structured_rerank` | 2 | 1.000 | true | true | 174 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `union_structured_rerank` | 3 | 1.000 | true | true | 278 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `task_aware_balanced_rerank` | 1 | 1.000 | true | true | 88 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `task_aware_balanced_rerank` | 2 | 1.000 | true | true | 174 |
| `topics.bug_fix.sample_benchmark_loader_tests` | `task_aware_balanced_rerank` | 3 | 1.000 | true | true | 278 |
| `topics.research.production_experiment_goal` | `lexical_retrieval_order` | 1 | 1.000 | true | true | 197 |
| `topics.research.production_experiment_goal` | `lexical_retrieval_order` | 2 | 1.000 | true | true | 564 |
| `topics.research.production_experiment_goal` | `lexical_retrieval_order` | 3 | 1.000 | true | true | 793 |
| `topics.research.production_experiment_goal` | `sparse_retrieval_order` | 1 | 1.000 | true | true | 197 |
| `topics.research.production_experiment_goal` | `sparse_retrieval_order` | 2 | 1.000 | true | true | 564 |
| `topics.research.production_experiment_goal` | `sparse_retrieval_order` | 3 | 1.000 | true | true | 564 |
| `topics.research.production_experiment_goal` | `anchor_then_tail` | 1 | 0.000 | false | false | 229 |
| `topics.research.production_experiment_goal` | `anchor_then_tail` | 2 | 0.000 | false | false | 435 |
| `topics.research.production_experiment_goal` | `anchor_then_tail` | 3 | 0.000 | false | false | 585 |
| `topics.research.production_experiment_goal` | `union_lexical_rerank` | 1 | 1.000 | true | true | 197 |
| `topics.research.production_experiment_goal` | `union_lexical_rerank` | 2 | 1.000 | true | true | 564 |
| `topics.research.production_experiment_goal` | `union_lexical_rerank` | 3 | 1.000 | true | true | 793 |
| `topics.research.production_experiment_goal` | `union_structured_rerank` | 1 | 1.000 | true | true | 197 |
| `topics.research.production_experiment_goal` | `union_structured_rerank` | 2 | 1.000 | true | true | 426 |
| `topics.research.production_experiment_goal` | `union_structured_rerank` | 3 | 1.000 | true | true | 535 |
| `topics.research.production_experiment_goal` | `task_aware_balanced_rerank` | 1 | 1.000 | true | true | 197 |
| `topics.research.production_experiment_goal` | `task_aware_balanced_rerank` | 2 | 1.000 | true | true | 426 |
| `topics.research.production_experiment_goal` | `task_aware_balanced_rerank` | 3 | 1.000 | true | true | 535 |

## Structured Diagnostics

### `topics.inspect.deepseek_architecture_lane`

| Variant | Path | Score | Why It Ranked |
|---|---|---:|---|
| `union_structured_rerank` | `architecture-advances-2026/docs/compressed-attention-promotion-goal.md:1-40` | 35.35 | path_overlap=13.00, filename_overlap=6.80, text_overlap=11.00, rare_term_coverage=1.75, area_bonus=2.80 |
| `union_structured_rerank` | `architecture-advances-2026/code/src/arch_adv_2026/compressed_attention_remediation_plan.py:91-130` | 34.55 | path_overlap=13.00, filename_overlap=6.80, text_overlap=8.80, rare_term_coverage=1.75, code_bonus=1.40, area_bonus=2.80 |
| `union_structured_rerank` | `architecture-advances-2026/code/src/arch_adv_2026/compressed_attention_promotion_memo.py:61-100` | 33.45 | path_overlap=13.00, filename_overlap=6.80, text_overlap=7.70, rare_term_coverage=1.75, code_bonus=1.40, area_bonus=2.80 |
| `union_structured_rerank` | `architecture-advances-2026/code/src/arch_adv_2026/compressed_attention_promotion_assessment.py:61-100` | 32.35 | path_overlap=13.00, filename_overlap=6.80, text_overlap=6.60, rare_term_coverage=1.75, code_bonus=1.40, area_bonus=2.80 |
| `union_structured_rerank` | `architecture-advances-2026/docs/compressed-attention.md:1-40` | 30.95 | path_overlap=13.00, filename_overlap=6.80, text_overlap=6.60, rare_term_coverage=1.75, area_bonus=2.80 |
| `union_lexical_rerank` | `architecture-advances-2026/docs/compressed-attention-promotion-goal.md:1-40` | 47.25 | score=47.25 |
| `union_lexical_rerank` | `architecture-advances-2026/code/src/arch_adv_2026/compressed_attention_promotion_memo.py:61-100` | 37.35 | score=37.35 |
| `union_lexical_rerank` | `architecture-advances-2026/code/src/arch_adv_2026/compressed_attention_remediation_plan.py:91-130` | 37.30 | score=37.30 |
| `union_lexical_rerank` | `architecture-advances-2026/code/src/arch_adv_2026/compressed_attention_promotion_assessment.py:61-100` | 37.05 | score=37.05 |
| `union_lexical_rerank` | `architecture-advances-2026/docs/compressed-attention.md:1-40` | 36.25 | score=36.25 |

### `topics.diagnose.llm_dev_verifier_flow`

| Variant | Path | Score | Why It Ranked |
|---|---|---:|---|
| `union_structured_rerank` | `llm-developments-2026/code/tests/test_real_retrieval.py:31-66` | 31.00 | path_overlap=7.80, text_overlap=17.60, rare_term_coverage=2.80, area_bonus=2.80 |
| `union_structured_rerank` | `llm-developments-2026/code/tests/test_harness_and_verifier.py:1-40` | 29.90 | path_overlap=13.00, filename_overlap=6.80, text_overlap=6.60, rare_term_coverage=0.70, area_bonus=2.80 |
| `union_structured_rerank` | `llm-developments-2026/code/src/llm_dev_2026/meta_verifier.py:1-40` | 29.10 | path_overlap=13.00, filename_overlap=6.80, text_overlap=4.40, rare_term_coverage=0.70, code_bonus=1.40, area_bonus=2.80 |
| `union_structured_rerank` | `llm-developments-2026/code/src/llm_dev_2026/meta_verifier.py:31-70` | 29.10 | path_overlap=13.00, filename_overlap=6.80, text_overlap=4.40, rare_term_coverage=0.70, code_bonus=1.40, area_bonus=2.80 |
| `union_structured_rerank` | `llm-developments-2026/code/README.md:1-40` | 25.55 | path_overlap=7.80, text_overlap=13.20, rare_term_coverage=1.75, area_bonus=2.80 |
| `union_lexical_rerank` | `llm-developments-2026/code/README.md:1-40` | 39.10 | score=39.10 |
| `union_lexical_rerank` | `llm-developments-2026/code/tests/test_harness_and_verifier.py:1-40` | 37.95 | score=37.95 |
| `union_lexical_rerank` | `llm-developments-2026/code/tests/test_real_retrieval.py:31-66` | 34.35 | score=34.35 |
| `union_lexical_rerank` | `llm-developments-2026/code/src/llm_dev_2026/meta_verifier.py:31-70` | 31.20 | score=31.20 |
| `union_lexical_rerank` | `llm-developments-2026/code/src/llm_dev_2026/meta_verifier.py:1-40` | 28.75 | score=28.75 |

### `topics.bug_fix.sample_benchmark_loader_tests`

| Variant | Path | Score | Why It Ranked |
|---|---|---:|---|
| `union_structured_rerank` | `llm-developments-2026/code/tests/test_benchmark_schema.py:1-40` | 22.57 | path_overlap=7.80, filename_overlap=6.80, text_overlap=3.30, rare_term_coverage=1.87, area_bonus=2.80 |
| `union_structured_rerank` | `llm-developments-2026/code/src/llm_dev_2026/benchmark_loader.py:1-25` | 22.00 | path_overlap=5.20, filename_overlap=6.80, text_overlap=4.40, rare_term_coverage=1.40, code_bonus=1.40, area_bonus=2.80 |
| `union_structured_rerank` | `llm-developments-2026/code/src/llm_dev_2026/benchmark_schema.py:1-40` | 18.70 | path_overlap=5.20, filename_overlap=6.80, text_overlap=1.10, rare_term_coverage=1.40, code_bonus=1.40, area_bonus=2.80 |
| `union_structured_rerank` | `llm-developments-2026/code/tests/test_real_retrieval.py:31-66` | 18.10 | path_overlap=2.60, text_overlap=9.90, rare_term_coverage=2.80, area_bonus=2.80 |
| `union_structured_rerank` | `llm-developments-2026/code/tests/test_harness_and_verifier.py:61-100` | 14.07 | path_overlap=5.20, filename_overlap=3.40, text_overlap=2.20, rare_term_coverage=0.47, area_bonus=2.80 |
| `union_lexical_rerank` | `llm-developments-2026/code/tests/test_benchmark_schema.py:1-40` | 22.45 | score=22.45 |
| `union_lexical_rerank` | `llm-developments-2026/code/src/llm_dev_2026/benchmark_loader.py:1-25` | 20.85 | score=20.85 |
| `union_lexical_rerank` | `llm-developments-2026/code/tests/test_real_retrieval.py:31-66` | 20.80 | score=20.80 |
| `union_lexical_rerank` | `llm-developments-2026/code/src/llm_dev_2026/benchmark_schema.py:1-40` | 15.75 | score=15.75 |
| `union_lexical_rerank` | `llm-developments-2026/code/tests/test_harness_and_verifier.py:61-100` | 12.90 | score=12.90 |

### `topics.research.production_experiment_goal`

| Variant | Path | Score | Why It Ranked |
|---|---|---:|---|
| `union_structured_rerank` | `llm-developments-2026/projects/production-scale-real-experiment-checklist.md:1-40` | 31.87 | path_overlap=7.80, filename_overlap=10.20, text_overlap=9.90, rare_term_coverage=1.17, area_bonus=2.80 |
| `union_structured_rerank` | `architecture-advances-2026/docs/compressed-attention-promotion-goal.md:1-40` | 21.80 | path_overlap=5.20, filename_overlap=6.80, text_overlap=6.60, synonym_text_overlap=1.80, rare_term_coverage=1.40 |
| `union_structured_rerank` | `llm-developments-2026/code/src/llm_dev_2026/real_retrieval.py:1-40` | 17.58 | path_overlap=2.60, filename_overlap=3.40, text_overlap=4.40, synonym_text_overlap=1.35, rare_term_coverage=1.63, code_bonus=1.40, area_bonus=2.80 |
| `union_structured_rerank` | `llm-developments-2026/code/src/llm_dev_2026/retrieval.py:31-70` | 17.27 | path_overlap=2.60, filename_overlap=3.40, text_overlap=6.60, rare_term_coverage=0.47, code_bonus=1.40, area_bonus=2.80 |
| `union_structured_rerank` | `llm-developments-2026/code/src/llm_dev_2026/experiment.py:1-40` | 16.93 | path_overlap=2.60, filename_overlap=3.40, text_overlap=3.30, synonym_text_overlap=1.80, rare_term_coverage=1.63, code_bonus=1.40, area_bonus=2.80 |
| `union_lexical_rerank` | `llm-developments-2026/projects/production-scale-real-experiment-checklist.md:1-40` | 35.65 | score=35.65 |
| `union_lexical_rerank` | `harness-design/end-to-end-goal.md:1-40` | 25.50 | score=25.50 |
| `union_lexical_rerank` | `architecture-advances-2026/docs/compressed-attention-promotion-goal.md:1-40` | 23.50 | score=23.50 |
| `union_lexical_rerank` | `llm-developments-2026/projects/meaty-end-to-end-goal.md:1-28` | 22.20 | score=22.20 |
| `union_lexical_rerank` | `llm-developments-2026/code/src/llm_dev_2026/retrieval.py:31-70` | 19.90 | score=19.90 |

