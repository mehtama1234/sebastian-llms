from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from .config import RetrievalMode
from .corpus import Benchmark
from .text import Vocabulary, concept_of, cosine, lexical_score, tokenize


@dataclass(slots=True)
class RetrievalResult:
    mode: str
    query: str
    ranked: list[tuple[str, float]]  # (doc_id, score), best first
    retrieval_ops: int  # deterministic cost proxy (scan/compare work units)
    shortlist: list[str] = field(default_factory=list)
    selector_scores: dict[str, float] = field(default_factory=dict)

    def top_k(self, k: int) -> list[str]:
        return [doc_id for doc_id, _ in self.ranked[:k]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "query": self.query,
            "ranked": [[d, round(s, 6)] for d, s in self.ranked],
            "retrieval_ops": self.retrieval_ops,
            "shortlist": self.shortlist,
            "selector_scores": {d: round(s, 6) for d, s in self.selector_scores.items()},
        }


def _tiebreak(doc_id: str) -> float:
    """Stable, query-independent tie-break in [0, 1).

    Without this, documents that all score ~0 for a no-signal query fall back to
    corpus authoring order, which can accidentally float a topically-relevant gold
    doc into top_k and read as a retrieval "hit" that never really happened. A
    content-independent hash makes a no-signal query behave like a genuine miss.
    """
    return int.from_bytes(hashlib.sha1(doc_id.encode()).digest()[:4], "big") / 0x100000000


def _jitter(seed: int, doc_id: str) -> float:
    """Small deterministic score perturbation for candidate diversity.

    Two candidates with different seeds break near-ties differently, so a gold
    document sitting just outside top_k on one attempt can enter it on another.
    This is the mechanism behind measurable multi-attempt recall gains.
    """
    if seed == 0:
        return 0.0
    h = hashlib.sha1(f"{seed}:{doc_id}".encode()).digest()
    # Map first 4 bytes to [-1, 1), then scale to a small fraction of typical scores.
    raw = int.from_bytes(h[:4], "big") / 0xFFFFFFFF
    return (raw - 0.5) * 0.05


def _lexical_ranking(bench: Benchmark, query: str, vocab: Vocabulary, seed: int) -> tuple[list[tuple[str, float]], int]:
    qvec = vocab.lexical_vector(tokenize(query))
    ranked = []
    ops = 0
    for doc in bench.documents:
        dvec = vocab.lexical_vector(doc.tokens())
        ops += min(len(qvec), len(dvec))
        score = lexical_score(qvec, dvec) + _jitter(seed, doc.id)
        ranked.append((doc.id, score))
    ranked.sort(key=lambda x: (x[1], _tiebreak(x[0])), reverse=True)
    return ranked, ops


def _vector_ranking(bench: Benchmark, query: str, vocab: Vocabulary, seed: int) -> tuple[list[tuple[str, float]], int]:
    qemb = vocab.embed(tokenize(query))
    ranked = []
    ops = 0
    for doc in bench.documents:
        demb = vocab.embed(doc.tokens())
        ops += vocab.concept_dim  # a full dense dot product per document
        score = cosine(qemb, demb) + _jitter(seed, doc.id)
        ranked.append((doc.id, score))
    ranked.sort(key=lambda x: (x[1], _tiebreak(x[0])), reverse=True)
    return ranked, ops


def _rrf_fuse(
    lexical: list[tuple[str, float]],
    vector: list[tuple[str, float]],
    *,
    k: int = 60,
) -> list[tuple[str, float]]:
    """Reciprocal-rank fusion. Rank-based, so the two score scales need no calibration."""
    rank_lex = {doc_id: i for i, (doc_id, _) in enumerate(lexical)}
    rank_vec = {doc_id: i for i, (doc_id, _) in enumerate(vector)}
    fused = {}
    for doc_id in set(rank_lex) | set(rank_vec):
        score = 0.0
        if doc_id in rank_lex:
            score += 1.0 / (k + rank_lex[doc_id] + 1)
        if doc_id in rank_vec:
            score += 1.0 / (k + rank_vec[doc_id] + 1)
        fused[doc_id] = score
    return sorted(fused.items(), key=lambda x: x[1], reverse=True)


def _selector_score(query_tokens: list[str], doc_tokens: list[str], vocab: Vocabulary) -> float:
    """Cheap sparse-index score.

    This is intentionally simpler than the exact retriever. It rewards exact rare
    token overlap and concept overlap, then hands only a shortlist to the more
    expensive rankers. That mirrors a practical sparse indexer: broad recall from
    a cheap gate, precise ordering from a slower second stage.
    """
    if not query_tokens or not doc_tokens:
        return 0.0
    q_counts = Counter(query_tokens)
    d_token_set = set(doc_tokens)
    exact_overlap = sum(vocab.idf(tok) * count for tok, count in q_counts.items() if tok in d_token_set)

    q_concepts = Counter(c for c in (concept_of(tok) for tok in query_tokens) if c is not None)
    d_concepts = Counter(c for c in (concept_of(tok) for tok in doc_tokens) if c is not None)
    concept_overlap = sum(q_concepts[c] * d_concepts.get(c, 0) for c in q_concepts)
    return float(exact_overlap + 0.6 * concept_overlap)


def _sparse_ranking(bench: Benchmark, query: str, vocab: Vocabulary, seed: int) -> tuple[list[tuple[str, float]], int, list[str], dict[str, float]]:
    query_tokens = tokenize(query)
    selector_ranked: list[tuple[str, float]] = []
    selector_scores: dict[str, float] = {}
    selector_ops = 0
    for doc in bench.documents:
        doc_tokens = doc.tokens()
        selector_ops += max(1, len(query_tokens) // 2)
        score = _selector_score(query_tokens, doc_tokens, vocab) + _jitter(seed, doc.id)
        selector_scores[doc.id] = score
        selector_ranked.append((doc.id, score))
    selector_ranked.sort(key=lambda x: (x[1], _tiebreak(x[0])), reverse=True)

    shortlist_size = min(len(selector_ranked), max(4, len(selector_ranked) // 4))
    shortlist = [doc_id for doc_id, _ in selector_ranked[:shortlist_size]]

    qlex = vocab.lexical_vector(query_tokens)
    qemb = vocab.embed(query_tokens)
    lex_ranked: list[tuple[str, float]] = []
    vec_ranked: list[tuple[str, float]] = []
    rerank_ops = 0
    for doc_id in shortlist:
        doc = bench.doc(doc_id)
        dvec = vocab.lexical_vector(doc.tokens())
        demb = vocab.embed(doc.tokens())
        rerank_ops += min(len(qlex), len(dvec)) + vocab.concept_dim
        lex_ranked.append((doc_id, lexical_score(qlex, dvec)))
        vec_ranked.append((doc_id, cosine(qemb, demb)))
    lex_ranked.sort(key=lambda x: (x[1], _tiebreak(x[0])), reverse=True)
    vec_ranked.sort(key=lambda x: (x[1], _tiebreak(x[0])), reverse=True)

    fused = dict(_rrf_fuse(lex_ranked, vec_ranked, k=20))
    reranked = [
        (doc_id, fused[doc_id] + 0.03 * selector_scores[doc_id] + _jitter(seed, doc_id))
        for doc_id in shortlist
    ]
    reranked.sort(key=lambda x: (x[1], _tiebreak(x[0])), reverse=True)

    tail = [(doc_id, selector_scores[doc_id]) for doc_id, _ in selector_ranked if doc_id not in shortlist]
    return reranked + tail, selector_ops + rerank_ops, shortlist, selector_scores


def retrieve(bench: Benchmark, query: str, mode: RetrievalMode, *, seed: int = 0) -> RetrievalResult:
    vocab = bench.vocab()
    shortlist: list[str] = []
    selector_scores: dict[str, float] = {}
    if mode is RetrievalMode.LEXICAL:
        ranked, ops = _lexical_ranking(bench, query, vocab, seed)
    elif mode is RetrievalMode.VECTOR:
        ranked, ops = _vector_ranking(bench, query, vocab, seed)
    elif mode is RetrievalMode.HYBRID:
        lex_ranked, lex_ops = _lexical_ranking(bench, query, vocab, seed)
        vec_ranked, vec_ops = _vector_ranking(bench, query, vocab, seed)
        ranked = _rrf_fuse(lex_ranked, vec_ranked)
        ops = lex_ops + vec_ops  # hybrid pays for both index scans
    elif mode is RetrievalMode.SPARSE:
        ranked, ops, shortlist, selector_scores = _sparse_ranking(bench, query, vocab, seed)
    else:  # pragma: no cover - exhaustive over the enum
        raise ValueError(f"unknown retrieval mode: {mode}")
    return RetrievalResult(
        mode=mode.value,
        query=query,
        ranked=ranked,
        retrieval_ops=ops,
        shortlist=shortlist,
        selector_scores=selector_scores,
    )
