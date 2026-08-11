from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import ContextPolicy
from .corpus import Benchmark, Document
from .instructions import InstructionLoad
from .text import tokenize


@dataclass(slots=True)
class AssembledContext:
    """The prompt context handed to the model for one attempt.

    Tracks token composition so experiments can report context pressure
    (Target A2), and records which evidence markers actually reached the prompt so
    the harness can tell real grounding from bluffing.
    """

    policy: str
    doc_ids: list[str]
    context_tokens: int
    instruction_tokens: int
    evidence_in_context: set[str] = field(default_factory=set)

    @property
    def prompt_tokens(self) -> int:
        return self.context_tokens + self.instruction_tokens

    def has_evidence(self, marker: str) -> bool:
        return marker.lower() in self.evidence_in_context

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy": self.policy,
            "doc_ids": self.doc_ids,
            "context_tokens": self.context_tokens,
            "instruction_tokens": self.instruction_tokens,
            "prompt_tokens": self.prompt_tokens,
            "evidence_in_context": sorted(self.evidence_in_context),
        }


def _snippet(tokens: list[str], query_tokens: set[str], window: int) -> list[str]:
    """A query-centered window over a token stream.

    The window is anchored on the first token that also appears in the query, so
    evidence far from the anchor (typically tail-placed markers) legitimately
    falls outside it. This is the cost the snippet policy pays for its token
    savings versus full inlining.
    """
    anchor = next((i for i, t in enumerate(tokens) if t in query_tokens), 0)
    half = max(1, window // 2)
    start = max(0, anchor - half)
    end = min(len(tokens), anchor + half + 1)
    return tokens[start:end]


def _doc_content(doc: Document, policy: ContextPolicy, query_tokens: set[str], window: int) -> tuple[list[str], bool]:
    """Return (tokens delivered for this doc, evidence marker present)."""
    marker = doc.evidence_token.lower()
    if policy is ContextPolicy.INLINE_FULL:
        toks = doc.positioned_body_tokens()
        return toks, bool(marker) and marker in toks
    if policy is ContextPolicy.INLINE_SNIPPET:
        toks = _snippet(doc.positioned_body_tokens(), query_tokens, window)
        return toks, bool(marker) and marker in toks
    if policy is ContextPolicy.POINTER:
        toks = doc.summary_tokens()
        return toks, bool(marker) and marker in toks
    raise ValueError(f"unknown context policy: {policy}")  # pragma: no cover


def assemble_context(
    bench: Benchmark,
    doc_ids: list[str],
    query: str,
    policy: ContextPolicy,
    instruction: InstructionLoad,
    *,
    snippet_window: int = 24,
) -> AssembledContext:
    query_tokens = set(tokenize(query))
    context_tokens = 0
    evidence: set[str] = set()
    for doc_id in doc_ids:
        doc = bench.doc(doc_id)
        toks, has_ev = _doc_content(doc, policy, query_tokens, snippet_window)
        context_tokens += len(toks)
        if has_ev:
            evidence.add(doc.evidence_token.lower())
    return AssembledContext(
        policy=policy.value,
        doc_ids=list(doc_ids),
        context_tokens=context_tokens,
        instruction_tokens=instruction.token_cost,
        evidence_in_context=evidence,
    )
