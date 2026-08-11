from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .text import Vocabulary, tokenize


@dataclass(slots=True)
class Document:
    """A synthetic repo file the retrieval layer can return.

    ``body`` is the file text *without* the evidence marker. ``summary`` is the
    one-line pointer payload used by the ``pointer`` context policy. ``area`` is
    the repo subtree, used by hierarchical instruction loading. ``evidence_token``
    is a unique marker; a task succeeds only when this marker reaches the
    assembled context.

    Evidence placement is what makes the context-policy comparison real:
      - ``evidence_head``: marker sits at the top of the body, so a query-centered
        snippet window can catch it. Otherwise it sits at the tail and only
        full-body inlining includes it.
      - ``evidence_in_summary``: marker is carried in the one-line summary, so the
        cheap pointer policy can still deliver it.
    """

    id: str
    area: str
    path: str
    summary: str
    body: str
    evidence_token: str = ""
    evidence_head: bool = False
    evidence_in_summary: bool = False

    def tokens(self) -> list[str]:
        # Retrieval scores the body only; the evidence marker never leaks into
        # ranking, so retrieval quality and context quality stay independent.
        return tokenize(self.body)

    def positioned_body_tokens(self) -> list[str]:
        toks = tokenize(self.body)
        marker = self.evidence_token.lower()
        if not marker:
            return toks
        return [marker, *toks] if self.evidence_head else [*toks, marker]

    def summary_tokens(self) -> list[str]:
        toks = tokenize(self.summary)
        if self.evidence_in_summary and self.evidence_token:
            toks.append(self.evidence_token.lower())
        return toks

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "area": self.area, "path": self.path}


@dataclass(slots=True)
class Scenario:
    """A benchmark task over the corpus.

    ``retrieval_favor`` records which retrieval mode the task is designed to
    reward, so scorecards can explain *why* a mode wins, not just that it does.
    ``needs_guidance`` marks tasks that cannot be solved without a repo
    instruction hint (``generic`` is satisfied by root or hierarchical loading;
    an area name requires hierarchical loading of that subtree).
    """

    id: str
    task_class: str
    query: str
    gold_doc_id: str
    retrieval_favor: str = "either"  # lexical | vector | either
    needs_guidance: str | None = None  # None | "generic" | area name
    difficulty: str = "easy"  # easy | hard (hard = gold sits at the top_k boundary)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "task_class": self.task_class,
            "retrieval_favor": self.retrieval_favor,
            "needs_guidance": self.needs_guidance,
            "difficulty": self.difficulty,
        }


@dataclass(slots=True)
class Benchmark:
    documents: list[Document]
    scenarios: list[Scenario]
    _vocab: Vocabulary | None = field(default=None, repr=False)

    def vocab(self) -> Vocabulary:
        if self._vocab is None:
            self._vocab = Vocabulary([doc.tokens() for doc in self.documents])
        return self._vocab

    def doc(self, doc_id: str) -> Document:
        for d in self.documents:
            if d.id == doc_id:
                return d
        raise KeyError(doc_id)


def _doc(id: str, area: str, summary: str, body: str, evidence: str) -> Document:
    return Document(
        id=id,
        area=area,
        path=f"{area}/{id}.py",
        summary=summary,
        body=body,
        evidence_token=evidence,
    )


def build_default_benchmark() -> Benchmark:
    """A small, self-contained repo corpus plus a scenario pack.

    The pack is engineered so the four production questions each have at least
    one decisive scenario:
      - lexical vs vector: synonym queries (vector) vs exact-identifier queries (lexical)
      - inline vs snippet vs pointer: evidence placed at the tail of long bodies
      - instruction loading: tasks that cannot be solved without a guidance hint
      - verifier / multi-attempt: hard scenarios where the gold doc sits at the
        top_k boundary and only re-attempts or fusion recover it
    """
    documents = [
        _doc(
            "retry_policy",
            "net",
            "How the network client reattempts failed requests with exponential backoff.",
            "the client will reattempt a failed request using exponential backoff and jitter "
            "before it resubmits to the upstream service after a transient error",
            "EVIDENCE_RETRY_BACKOFF",
        ),
        _doc(
            "http_client",
            "net",
            "Core HTTP client that sends requests and reads responses.",
            "the http client opens a socket sends the request body and reads the response "
            "headers then returns a decoded payload to the caller",
            "EVIDENCE_HTTP_CORE",
        ),
        _doc(
            "auth_login",
            "auth",
            "User authentication and credential exchange.",
            "the authentication module exchanges a user secret for a session token and "
            "refreshes the token before expiry using a stored refresh secret",
            "EVIDENCE_AUTH_SESSION",
        ),
        _doc(
            "token_cache",
            "auth",
            "Caches issued session tokens to avoid re-authentication.",
            "the token cache memoizes issued session tokens keyed by user so repeated calls "
            "skip authentication until the cached entry passes its deadline",
            "EVIDENCE_TOKEN_CACHE",
        ),
        _doc(
            "config_parser",
            "config",
            "Parses the layered configuration files.",
            "the parse_config_v2 routine deserializes layered configuration files merges "
            "settings and validates required options before startup",
            "EVIDENCE_CONFIG_PARSE",
        ),
        _doc(
            "settings_store",
            "config",
            "Holds resolved configuration options at runtime.",
            "the settings store keeps resolved configuration options in memory and exposes "
            "typed getters for other modules to read validated values",
            "EVIDENCE_SETTINGS_STORE",
        ),
        _doc(
            "response_cache",
            "cache",
            "Memoizes upstream responses to cut repeat calls.",
            "the response cache memoizes upstream responses keyed by request signature and "
            "evicts entries once they pass their expiration deadline",
            "EVIDENCE_RESPONSE_CACHE",
        ),
        _doc(
            "crypto_box",
            "crypto",
            "Encrypts sensitive payloads at rest.",
            "the crypto box encrypts sensitive payloads with an authenticated cipher and "
            "rotates the encryption key on a fixed schedule",
            "EVIDENCE_CRYPTO_BOX",
        ),
        _doc(
            "worker_pool",
            "runtime",
            "Runs tasks across a pool of async workers.",
            "the worker pool runs tasks in parallel across async workers and bounds "
            "concurrency with a semaphore to avoid overload",
            "EVIDENCE_WORKER_POOL",
        ),
        _doc(
            "telemetry",
            "obs",
            "Structured logging and request tracing.",
            "the telemetry layer emits structured logging and trace spans for each request "
            "so operators can follow a call across services",
            "EVIDENCE_TELEMETRY",
        ),
        _doc(
            "request_validator",
            "net",
            "Validates inbound request payloads.",
            "the request validator verifies inbound payloads against a schema and rejects "
            "malformed input before it reaches the handler",
            "EVIDENCE_REQ_VALIDATOR",
        ),
        _doc(
            "deadline_guard",
            "runtime",
            "Cancels work that exceeds its deadline.",
            "the deadline_guard_v3 routine cancels in-flight work once it exceeds the configured "
            "timeout and records the expiration for later inspection",
            "EVIDENCE_DEADLINE_GUARD",
        ),
    ]

    scenarios = [
        # Synonym queries: the query word is absent from the gold body, present only
        # as a concept sibling. Vector retrieval should win, lexical should struggle.
        Scenario("s_retry_syn", "diagnose", "why does the client retry on timeout",
                 "retry_policy", retrieval_favor="vector", difficulty="hard"),
        Scenario("s_auth_syn", "inspect", "where do we handle login credentials",
                 "auth_login", retrieval_favor="vector"),
        Scenario("s_cache_syn", "inspect", "what does memoization of responses do",
                 "response_cache", retrieval_favor="vector"),
        # Exact-identifier queries with no concept words: the concept-space embedding
        # is blind to them, so vector degenerates and lexical wins outright.
        Scenario("s_config_id", "fix", "parse_config_v2 stacktrace regression",
                 "config_parser", retrieval_favor="lexical"),
        Scenario("s_deadline_id", "diagnose", "deadline_guard_v3 crash regression",
                 "deadline_guard", retrieval_favor="lexical"),
        # Either mode should find these; they mainly exercise context/verifier policy.
        Scenario("s_crypto", "inspect", "how are payloads encrypted with a cipher",
                 "crypto_box", retrieval_favor="either"),
        Scenario("s_worker", "inspect", "how is concurrency bounded across async workers",
                 "worker_pool", retrieval_favor="either"),
        Scenario("s_validate", "fix", "request validator rejects malformed schema input",
                 "request_validator", retrieval_favor="either"),
        Scenario("s_telemetry", "inspect", "where is structured logging and tracing emitted",
                 "telemetry", retrieval_favor="either"),
        Scenario("s_token_cache", "diagnose", "token cache memoize skip authentication deadline",
                 "token_cache", retrieval_favor="either", difficulty="hard"),
        # Guidance-dependent tasks: unsolvable without an instruction hint.
        Scenario("s_settings_guided", "feature", "add a new resolved configuration option",
                 "settings_store", retrieval_favor="either", needs_guidance="generic"),
        Scenario("s_http_guided", "feature", "extend the http client response decoding",
                 "http_client", retrieval_favor="either", needs_guidance="net"),
    ]

    # Spread evidence placement so no single context policy trivially wins.
    # Roughly one third of documents carry evidence in the head (snippet-catchable)
    # and in the summary (pointer-catchable); the rest keep it at the tail, where
    # only full-body inlining includes it. This yields the intended aggregate
    # tradeoff: inline_full = highest recall / highest tokens, snippet = cheaper /
    # partial recall, pointer = cheapest / lowest recall.
    for i, doc in enumerate(documents):
        if i % 3 == 0:
            doc.evidence_head = True
            doc.evidence_in_summary = True
        elif i % 3 == 1:
            doc.evidence_head = True

    return Benchmark(documents=documents, scenarios=scenarios)
