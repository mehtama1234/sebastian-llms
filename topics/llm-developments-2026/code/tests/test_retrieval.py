from __future__ import annotations

from llm_dev_2026.config import RetrievalMode
from llm_dev_2026.retrieval import retrieve


def _rank_of(bench, query, mode, doc_id, seed=0):
    result = retrieve(bench, query, mode, seed=seed)
    return [d for d, _ in result.ranked].index(doc_id)


def test_vector_recovers_paraphrase_query_lexical_misses(bench):
    # s_retry_syn: query uses "retry"/"timeout"; gold body uses "reattempt"/"backoff".
    scenario = next(s for s in bench.scenarios if s.id == "s_retry_syn")
    lex_top = retrieve(bench, scenario.query, RetrievalMode.LEXICAL).top_k(3)
    vec_top = retrieve(bench, scenario.query, RetrievalMode.VECTOR).top_k(3)
    assert scenario.gold_doc_id not in lex_top  # lexical is blind to the synonyms
    assert scenario.gold_doc_id in vec_top  # concept-space bridges them


def test_lexical_wins_on_exact_identifier_vector_is_blind(bench):
    # s_config_id / s_deadline_id: identifier queries with no concept words.
    for sid in ("s_config_id", "s_deadline_id"):
        scenario = next(s for s in bench.scenarios if s.id == sid)
        lex_top = retrieve(bench, scenario.query, RetrievalMode.LEXICAL).top_k(3)
        vec_top = retrieve(bench, scenario.query, RetrievalMode.VECTOR).top_k(3)
        assert scenario.gold_doc_id in lex_top
        assert scenario.gold_doc_id not in vec_top


def test_hybrid_keeps_at_least_one_mode_win(bench):
    scenario = next(s for s in bench.scenarios if s.id == "s_retry_syn")
    hyb_top = retrieve(bench, scenario.query, RetrievalMode.HYBRID).top_k(3)
    assert scenario.gold_doc_id in hyb_top


def test_sparse_shortlist_keeps_semantic_and_identifier_wins(bench):
    for sid in ("s_retry_syn", "s_config_id"):
        scenario = next(s for s in bench.scenarios if s.id == sid)
        result = retrieve(bench, scenario.query, RetrievalMode.SPARSE)
        assert scenario.gold_doc_id in result.shortlist
        assert scenario.gold_doc_id in result.top_k(3)


def test_hybrid_pays_for_both_scans(bench):
    q = "how does caching work"
    lex = retrieve(bench, q, RetrievalMode.LEXICAL)
    vec = retrieve(bench, q, RetrievalMode.VECTOR)
    hyb = retrieve(bench, q, RetrievalMode.HYBRID)
    assert hyb.retrieval_ops == lex.retrieval_ops + vec.retrieval_ops


def test_sparse_costs_less_than_full_hybrid_scan(bench):
    q = "why does the client retry on timeout"
    hyb = retrieve(bench, q, RetrievalMode.HYBRID)
    sparse = retrieve(bench, q, RetrievalMode.SPARSE)
    assert sparse.retrieval_ops < hyb.retrieval_ops


def test_seed_jitter_can_reorder_near_ties(bench):
    # Different seeds must be able to produce different rankings, or multi-attempt
    # recall gains would be impossible.
    q = "how is concurrency bounded across async workers"
    rankings = {tuple(retrieve(bench, q, RetrievalMode.LEXICAL, seed=s).top_k(5)) for s in range(6)}
    assert len(rankings) > 1


def test_seed_zero_is_deterministic(bench):
    q = "authentication session token"
    a = retrieve(bench, q, RetrievalMode.VECTOR, seed=0).ranked
    b = retrieve(bench, q, RetrievalMode.VECTOR, seed=0).ranked
    assert a == b
