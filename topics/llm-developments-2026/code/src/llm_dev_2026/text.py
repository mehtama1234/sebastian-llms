from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable, Sequence

import numpy as np

_TOKEN_RE = re.compile(r"[a-z0-9_]+")

# Surface tokens that share a concept. Vector retrieval embeds into this concept
# space, so a query written with one surface form ("retry") can still match a
# document written with a synonym ("reattempt", "backoff"). Lexical retrieval,
# which scores raw token overlap, cannot bridge these. This is the mechanism that
# makes the retrieval-mode comparison produce a real, paper-consistent tradeoff
# rather than a tie.
_CONCEPT_GROUPS: dict[str, tuple[str, ...]] = {
    "retry": ("retry", "reattempt", "backoff", "resubmit"),
    "auth": ("auth", "authentication", "login", "credentials"),
    "cache": ("cache", "caching", "memoize", "memoization"),
    "timeout": ("timeout", "deadline", "expiry", "expiration"),
    "parse": ("parse", "parsing", "deserialize", "decode"),
    "validate": ("validate", "validation", "verify", "check"),
    "concurrency": ("concurrency", "parallel", "async", "threads"),
    "config": ("config", "configuration", "settings", "options"),
    "logging": ("logging", "log", "trace", "telemetry"),
    "encrypt": ("encrypt", "encryption", "cipher", "crypto"),
}

_SURFACE_TO_CONCEPT: dict[str, str] = {
    surface: concept for concept, surfaces in _CONCEPT_GROUPS.items() for surface in surfaces
}


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


KNOWN_CONCEPTS: tuple[str, ...] = tuple(sorted(_CONCEPT_GROUPS))


def concept_of(token: str) -> str | None:
    """Map a surface token to its concept, or ``None`` if the token is unmapped.

    This is a deliberate caricature of the lexical/vector duality. Rare exact
    identifiers (e.g. ``parse_config_v2``) belong to no concept group, so the
    concept-space embedding drops them entirely and is *blind* to them. A query
    made of such identifiers embeds to a near-zero vector and vector retrieval
    degenerates, while lexical retrieval still matches the exact token. Symmetrically,
    a synonym query (``retry`` for a doc that says ``reattempt``) carries concept
    mass that lexical overlap cannot see. Real embeddings blur rather than fully
    drop rare tokens; this cleaner version makes the tradeoff decisive and
    testable, and the harness notes say so.
    """
    return _SURFACE_TO_CONCEPT.get(token)


def _concept_space(tokens: Iterable[str]) -> Counter[str]:
    return Counter(c for c in (concept_of(t) for t in tokens) if c is not None)


class Vocabulary:
    """Shared vocabulary and IDF table computed once over a document set.

    Holds both a lexical IDF table (raw tokens) and a stable concept-dimension
    index so vector embeddings are comparable across documents and queries.
    """

    def __init__(self, documents: Sequence[Sequence[str]]) -> None:
        self._doc_count = max(1, len(documents))
        df: Counter[str] = Counter()
        concept_df: Counter[str] = Counter()
        for tokens in documents:
            for tok in set(tokens):
                df[tok] += 1
            for concept in _concept_space(tokens):
                concept_df[concept] += 1
        self._df = df
        self._idf = {
            tok: math.log((self._doc_count + 1) / (count + 1)) + 1.0 for tok, count in df.items()
        }
        # Embedding dims are the fixed known-concept set, not whatever the corpus
        # happened to contain, so query-only concepts are always representable and
        # embeddings from different corpora stay comparable.
        self._concept_idf = {
            concept: math.log((self._doc_count + 1) / (concept_df.get(concept, 0) + 1)) + 1.0
            for concept in KNOWN_CONCEPTS
        }
        self._concept_index = {concept: i for i, concept in enumerate(KNOWN_CONCEPTS)}

    @property
    def concept_dim(self) -> int:
        return len(self._concept_index)

    def idf(self, token: str) -> float:
        # Unseen query tokens still carry maximal weight: an exact identifier that
        # appears in only one document should dominate lexical scoring.
        return self._idf.get(token, math.log(self._doc_count + 1) + 1.0)

    def lexical_vector(self, tokens: Sequence[str]) -> Counter[str]:
        """IDF-weighted bag of raw tokens."""
        counts = Counter(tokens)
        return Counter({tok: count * self.idf(tok) for tok, count in counts.items()})

    def embed(self, tokens: Sequence[str]) -> np.ndarray:
        """IDF-weighted concept-space embedding, L2-normalized."""
        vec = np.zeros(self.concept_dim, dtype=np.float64)
        for concept, count in _concept_space(tokens).items():
            idx = self._concept_index.get(concept)
            if idx is None:
                continue  # concept unseen at fit time (query-only tokens); skip
            weight = self._concept_idf.get(concept, 1.0)
            vec[idx] = count * weight
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec


def lexical_score(query_vec: Counter[str], doc_vec: Counter[str]) -> float:
    """Dot product over shared raw tokens (unnormalized cosine numerator)."""
    if len(query_vec) > len(doc_vec):
        query_vec, doc_vec = doc_vec, query_vec
    return float(sum(weight * doc_vec.get(tok, 0.0) for tok, weight in query_vec.items()))


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))  # inputs are pre-normalized by ``Vocabulary.embed``
