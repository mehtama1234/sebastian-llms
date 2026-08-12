# Indexer vs Attention Report

## Summary

| Variant | Mean Support Recall | Mean Answer Accuracy | Budgets |
|---|---:|---:|---|
| `fuller_context_baseline` | 0.300 | 0.333 | 1, 2, 3 |
| `window_plus_anchor` | 0.200 | 0.267 | 1, 2, 3 |
| `sparse_indexer_lexical` | 0.900 | 0.933 | 1, 2, 3 |
| `sparse_indexer_mixed` | 0.833 | 0.867 | 1, 2, 3 |
| `sparse_indexer_structured` | 0.900 | 0.933 | 1, 2, 3 |
| `compressed_attention_reference` | 0.567 | 0.600 | 1, 2, 3 |

## Rows

| Task | Variant | Budget | Recall | Exact Hit | Answer Correct |
|---|---|---:|---:|---:|---:|
| `lc_passkey` | `fuller_context_baseline` | 1 | 0.000 | false | false |
| `lc_passkey` | `fuller_context_baseline` | 2 | 0.000 | false | false |
| `lc_passkey` | `fuller_context_baseline` | 3 | 1.000 | true | true |
| `lc_passkey` | `window_plus_anchor` | 1 | 0.000 | false | false |
| `lc_passkey` | `window_plus_anchor` | 2 | 0.000 | false | false |
| `lc_passkey` | `window_plus_anchor` | 3 | 1.000 | true | true |
| `lc_passkey` | `sparse_indexer_lexical` | 1 | 1.000 | true | true |
| `lc_passkey` | `sparse_indexer_lexical` | 2 | 1.000 | true | true |
| `lc_passkey` | `sparse_indexer_lexical` | 3 | 1.000 | true | true |
| `lc_passkey` | `sparse_indexer_mixed` | 1 | 1.000 | true | true |
| `lc_passkey` | `sparse_indexer_mixed` | 2 | 1.000 | true | true |
| `lc_passkey` | `sparse_indexer_mixed` | 3 | 1.000 | true | true |
| `lc_passkey` | `sparse_indexer_structured` | 1 | 1.000 | true | true |
| `lc_passkey` | `sparse_indexer_structured` | 2 | 1.000 | true | true |
| `lc_passkey` | `sparse_indexer_structured` | 3 | 1.000 | true | true |
| `lc_passkey` | `compressed_attention_reference` | 1 | 0.000 | false | false |
| `lc_passkey` | `compressed_attention_reference` | 2 | 1.000 | true | true |
| `lc_passkey` | `compressed_attention_reference` | 3 | 1.000 | true | true |
| `lc_multihop` | `fuller_context_baseline` | 1 | 0.000 | false | false |
| `lc_multihop` | `fuller_context_baseline` | 2 | 0.500 | false | false |
| `lc_multihop` | `fuller_context_baseline` | 3 | 0.500 | false | false |
| `lc_multihop` | `window_plus_anchor` | 1 | 0.000 | false | false |
| `lc_multihop` | `window_plus_anchor` | 2 | 0.000 | false | false |
| `lc_multihop` | `window_plus_anchor` | 3 | 0.500 | false | false |
| `lc_multihop` | `sparse_indexer_lexical` | 1 | 0.500 | false | false |
| `lc_multihop` | `sparse_indexer_lexical` | 2 | 1.000 | true | true |
| `lc_multihop` | `sparse_indexer_lexical` | 3 | 1.000 | true | true |
| `lc_multihop` | `sparse_indexer_mixed` | 1 | 0.500 | false | false |
| `lc_multihop` | `sparse_indexer_mixed` | 2 | 1.000 | true | true |
| `lc_multihop` | `sparse_indexer_mixed` | 3 | 1.000 | true | true |
| `lc_multihop` | `sparse_indexer_structured` | 1 | 0.500 | false | false |
| `lc_multihop` | `sparse_indexer_structured` | 2 | 1.000 | true | true |
| `lc_multihop` | `sparse_indexer_structured` | 3 | 1.000 | true | true |
| `lc_multihop` | `compressed_attention_reference` | 1 | 0.000 | false | false |
| `lc_multihop` | `compressed_attention_reference` | 2 | 0.500 | false | false |
| `lc_multihop` | `compressed_attention_reference` | 3 | 1.000 | true | true |
| `lc_distractor_heavy` | `fuller_context_baseline` | 1 | 0.000 | false | false |
| `lc_distractor_heavy` | `fuller_context_baseline` | 2 | 0.000 | false | false |
| `lc_distractor_heavy` | `fuller_context_baseline` | 3 | 1.000 | true | true |
| `lc_distractor_heavy` | `window_plus_anchor` | 1 | 0.000 | false | false |
| `lc_distractor_heavy` | `window_plus_anchor` | 2 | 0.000 | false | false |
| `lc_distractor_heavy` | `window_plus_anchor` | 3 | 0.000 | false | false |
| `lc_distractor_heavy` | `sparse_indexer_lexical` | 1 | 1.000 | true | true |
| `lc_distractor_heavy` | `sparse_indexer_lexical` | 2 | 1.000 | true | true |
| `lc_distractor_heavy` | `sparse_indexer_lexical` | 3 | 1.000 | true | true |
| `lc_distractor_heavy` | `sparse_indexer_mixed` | 1 | 1.000 | true | true |
| `lc_distractor_heavy` | `sparse_indexer_mixed` | 2 | 1.000 | true | true |
| `lc_distractor_heavy` | `sparse_indexer_mixed` | 3 | 1.000 | true | true |
| `lc_distractor_heavy` | `sparse_indexer_structured` | 1 | 1.000 | true | true |
| `lc_distractor_heavy` | `sparse_indexer_structured` | 2 | 1.000 | true | true |
| `lc_distractor_heavy` | `sparse_indexer_structured` | 3 | 1.000 | true | true |
| `lc_distractor_heavy` | `compressed_attention_reference` | 1 | 0.000 | false | false |
| `lc_distractor_heavy` | `compressed_attention_reference` | 2 | 1.000 | true | true |
| `lc_distractor_heavy` | `compressed_attention_reference` | 3 | 1.000 | true | true |
| `lc_synonym_bridge` | `fuller_context_baseline` | 1 | 0.000 | false | false |
| `lc_synonym_bridge` | `fuller_context_baseline` | 2 | 0.000 | false | false |
| `lc_synonym_bridge` | `fuller_context_baseline` | 3 | 0.500 | false | true |
| `lc_synonym_bridge` | `window_plus_anchor` | 1 | 0.000 | false | false |
| `lc_synonym_bridge` | `window_plus_anchor` | 2 | 0.500 | false | true |
| `lc_synonym_bridge` | `window_plus_anchor` | 3 | 0.500 | false | true |
| `lc_synonym_bridge` | `sparse_indexer_lexical` | 1 | 0.500 | false | true |
| `lc_synonym_bridge` | `sparse_indexer_lexical` | 2 | 1.000 | true | true |
| `lc_synonym_bridge` | `sparse_indexer_lexical` | 3 | 1.000 | true | true |
| `lc_synonym_bridge` | `sparse_indexer_mixed` | 1 | 0.000 | false | false |
| `lc_synonym_bridge` | `sparse_indexer_mixed` | 2 | 0.500 | false | true |
| `lc_synonym_bridge` | `sparse_indexer_mixed` | 3 | 1.000 | true | true |
| `lc_synonym_bridge` | `sparse_indexer_structured` | 1 | 0.500 | false | true |
| `lc_synonym_bridge` | `sparse_indexer_structured` | 2 | 1.000 | true | true |
| `lc_synonym_bridge` | `sparse_indexer_structured` | 3 | 1.000 | true | true |
| `lc_synonym_bridge` | `compressed_attention_reference` | 1 | 0.000 | false | false |
| `lc_synonym_bridge` | `compressed_attention_reference` | 2 | 0.500 | false | true |
| `lc_synonym_bridge` | `compressed_attention_reference` | 3 | 1.000 | true | true |
| `lc_verifier_chain` | `fuller_context_baseline` | 1 | 0.000 | false | false |
| `lc_verifier_chain` | `fuller_context_baseline` | 2 | 0.500 | false | true |
| `lc_verifier_chain` | `fuller_context_baseline` | 3 | 0.500 | false | true |
| `lc_verifier_chain` | `window_plus_anchor` | 1 | 0.000 | false | false |
| `lc_verifier_chain` | `window_plus_anchor` | 2 | 0.000 | false | false |
| `lc_verifier_chain` | `window_plus_anchor` | 3 | 0.500 | false | true |
| `lc_verifier_chain` | `sparse_indexer_lexical` | 1 | 0.500 | false | true |
| `lc_verifier_chain` | `sparse_indexer_lexical` | 2 | 1.000 | true | true |
| `lc_verifier_chain` | `sparse_indexer_lexical` | 3 | 1.000 | true | true |
| `lc_verifier_chain` | `sparse_indexer_mixed` | 1 | 0.500 | false | true |
| `lc_verifier_chain` | `sparse_indexer_mixed` | 2 | 1.000 | true | true |
| `lc_verifier_chain` | `sparse_indexer_mixed` | 3 | 1.000 | true | true |
| `lc_verifier_chain` | `sparse_indexer_structured` | 1 | 0.500 | false | true |
| `lc_verifier_chain` | `sparse_indexer_structured` | 2 | 1.000 | true | true |
| `lc_verifier_chain` | `sparse_indexer_structured` | 3 | 1.000 | true | true |
| `lc_verifier_chain` | `compressed_attention_reference` | 1 | 0.000 | false | false |
| `lc_verifier_chain` | `compressed_attention_reference` | 2 | 0.500 | false | true |
| `lc_verifier_chain` | `compressed_attention_reference` | 3 | 1.000 | true | true |

## Structured Indexer Diagnostics

### `lc_passkey`

| Variant | Chunk | Role | Score | Why It Ranked |
|---|---|---|---:|---|
| `sparse_indexer_structured` | `s_passkey` (logs/archive.txt) | `support` | 13.00 | path_overlap=2.40, text_overlap=3.60, rare_term_coverage=2.80, phrase_hint=1.00, role_bonus=2.00, bridge_bonus=1.20 |
| `sparse_indexer_structured` | `a_overview` (docs/overview.md) | `anchor` | 1.53 | text_overlap=1.20, rare_term_coverage=0.93, phrase_hint=0.40, role_bonus=0.20 |
| `sparse_indexer_structured` | `d_2` (logs/day2.txt) | `distractor` | 0.00 | score-only |
| `sparse_indexer_mixed` | `s_passkey` (logs/archive.txt) | `support` | 7.40 | score=7.40 |
| `sparse_indexer_mixed` | `a_overview` (docs/overview.md) | `anchor` | 2.00 | score=2.00 |
| `sparse_indexer_mixed` | `d_2` (logs/day2.txt) | `distractor` | 0.00 | score-only |

### `lc_multihop`

| Variant | Chunk | Role | Score | Why It Ranked |
|---|---|---|---:|---|
| `sparse_indexer_structured` | `s_route` (control/route_planner.py) | `support` | 23.74 | path_overlap=9.00, text_overlap=8.60, rare_term_coverage=1.94, phrase_hint=1.00, role_bonus=2.00, bridge_bonus=1.20 |
| `sparse_indexer_structured` | `s_guard` (control/token_guard.py) | `support` | 18.24 | path_overlap=6.60, text_overlap=5.50, rare_term_coverage=1.94, phrase_hint=1.00, role_bonus=2.00, bridge_bonus=1.20 |
| `sparse_indexer_structured` | `d_3` (control/scheduler.py) | `distractor` | 5.66 | path_overlap=4.20, rare_term_coverage=0.86, phrase_hint=0.60 |
| `sparse_indexer_mixed` | `s_route` (control/route_planner.py) | `support` | 27.90 | score=27.90 |
| `sparse_indexer_mixed` | `s_guard` (control/token_guard.py) | `support` | 19.90 | score=19.90 |
| `sparse_indexer_mixed` | `a_runtime` (docs/runtime.md) | `anchor` | 9.50 | score=9.50 |

### `lc_distractor_heavy`

| Variant | Chunk | Role | Score | Why It Ranked |
|---|---|---|---:|---|
| `sparse_indexer_structured` | `s_marker` (archives/marker_registry.py) | `support` | 19.24 | path_overlap=4.20, text_overlap=8.60, rare_term_coverage=2.24, phrase_hint=1.00, role_bonus=2.00, bridge_bonus=1.20 |
| `sparse_indexer_structured` | `d_6` (archives/coastal_plan.md) | `distractor` | 13.11 | path_overlap=3.60, text_overlap=6.55, rare_term_coverage=1.96, phrase_hint=1.00 |
| `sparse_indexer_structured` | `d_5` (archives/notes.md) | `distractor` | 3.77 | text_overlap=2.25, rare_term_coverage=1.12, phrase_hint=0.40 |
| `sparse_indexer_mixed` | `s_marker` (archives/marker_registry.py) | `support` | 23.90 | score=23.90 |
| `sparse_indexer_mixed` | `d_6` (archives/coastal_plan.md) | `distractor` | 19.50 | score=19.50 |
| `sparse_indexer_mixed` | `d_5` (archives/notes.md) | `distractor` | 6.00 | score=6.00 |

### `lc_synonym_bridge`

| Variant | Chunk | Role | Score | Why It Ranked |
|---|---|---|---:|---|
| `sparse_indexer_structured` | `s_incident` (signals/failover_route.py) | `support` | 9.85 | text_overlap=4.85, rare_term_coverage=1.40, phrase_hint=0.40, role_bonus=2.00, bridge_bonus=1.20 |
| `sparse_indexer_structured` | `s_gate` (signals/sentinel_gate.py) | `support` | 9.15 | text_overlap=4.50, rare_term_coverage=1.05, phrase_hint=0.40, role_bonus=2.00, bridge_bonus=1.20 |
| `sparse_indexer_structured` | `a_signals` (signals/README.md) | `anchor` | 7.40 | text_overlap=5.90, rare_term_coverage=2.10, phrase_hint=0.40, role_bonus=0.20 |
| `sparse_indexer_mixed` | `a_signals` (signals/README.md) | `anchor` | 18.50 | score=18.50 |
| `sparse_indexer_mixed` | `s_incident` (signals/failover_route.py) | `support` | 14.40 | score=14.40 |
| `sparse_indexer_mixed` | `s_gate` (signals/sentinel_gate.py) | `support` | 12.90 | score=12.90 |

### `lc_verifier_chain`

| Variant | Chunk | Role | Score | Why It Ranked |
|---|---|---|---:|---|
| `sparse_indexer_structured` | `s_verifier` (checks/final_verifier.py) | `support` | 13.46 | path_overlap=2.40, text_overlap=6.00, rare_term_coverage=0.86, phrase_hint=1.00, role_bonus=2.00, bridge_bonus=1.20 |
| `sparse_indexer_structured` | `s_solver` (checks/draft_solver.py) | `support` | 13.25 | path_overlap=4.80, text_overlap=4.80, rare_term_coverage=0.65, phrase_hint=1.00, role_bonus=2.00 |
| `sparse_indexer_structured` | `a_checks` (checks/README.md) | `anchor` | 2.23 | text_overlap=2.40, rare_term_coverage=0.43, phrase_hint=0.40, role_bonus=0.20 |
| `sparse_indexer_mixed` | `s_solver` (checks/draft_solver.py) | `support` | 10.90 | score=10.90 |
| `sparse_indexer_mixed` | `s_verifier` (checks/final_verifier.py) | `support` | 10.40 | score=10.40 |
| `sparse_indexer_mixed` | `a_checks` (checks/README.md) | `anchor` | 3.50 | score=3.50 |

