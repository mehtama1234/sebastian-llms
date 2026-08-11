from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class RetrievalMode(str, Enum):
    """How the harness finds candidate documents for a query.

    - ``lexical``: token-overlap scoring. Strong on exact identifiers, weak on
      vocabulary mismatch (synonyms, paraphrase).
    - ``vector``: concept-space cosine similarity. Bridges vocabulary mismatch,
      weaker on rare exact tokens that collapse into generic buckets.
    - ``hybrid``: reciprocal-rank fusion of both. Aims to keep each mode's wins.
    - ``sparse``: cheap lexical/concept selector followed by exact reranking on a
      small shortlist. This is the harness analogue of a sparse indexer.
    """

    LEXICAL = "lexical"
    VECTOR = "vector"
    HYBRID = "hybrid"
    SPARSE = "sparse"


class ContextPolicy(str, Enum):
    """How retrieved documents are turned into prompt context.

    - ``inline_full``: paste whole documents. Highest evidence recall, highest
      token cost.
    - ``inline_snippet``: paste a query-centered window. Cheaper, but can drop
      evidence that sits outside the window.
    - ``pointer``: hand back a file pointer plus a one-line summary. Cheapest,
      relies on the summary carrying the evidence token.
    """

    INLINE_FULL = "inline_full"
    INLINE_SNIPPET = "inline_snippet"
    POINTER = "pointer"


class InstructionMode(str, Enum):
    """Repo-instruction (AGENTS.md-style) loading policy.

    - ``none``: no guidance file.
    - ``root``: one root instruction file loaded on every task.
    - ``hierarchical``: root plus subtree files, loaded only for the matching
      repo area / task class.
    """

    NONE = "none"
    ROOT = "root"
    HIERARCHICAL = "hierarchical"


@dataclass(slots=True)
class HarnessConfig:
    """A single point in the harness configuration space.

    One ``HarnessConfig`` is a serializable, comparable description of the policy
    knobs a coding-agent harness exposes. Experiments sweep this space and score
    which points are production-worthy.
    """

    name: str
    retrieval_mode: RetrievalMode = RetrievalMode.LEXICAL
    context_policy: ContextPolicy = ContextPolicy.INLINE_FULL
    instruction_mode: InstructionMode = InstructionMode.NONE
    top_k: int = 3
    snippet_window: int = 24
    # Test-time scaling knobs.
    candidate_count: int = 1
    share_evidence: bool = False
    # Verifier / stop-and-escalate knobs.
    verifier_enabled: bool = False
    meta_verifier_enabled: bool = False
    confidence_threshold: float = 0.5
    max_retries: int = 0

    def __post_init__(self) -> None:
        # Enums may arrive as raw strings from JSON; normalize so comparisons and
        # ``.value`` access always work.
        self.retrieval_mode = RetrievalMode(self.retrieval_mode)
        self.context_policy = ContextPolicy(self.context_policy)
        self.instruction_mode = InstructionMode(self.instruction_mode)
        if self.top_k <= 0:
            raise ValueError("top_k must be positive")
        if self.snippet_window <= 0:
            raise ValueError("snippet_window must be positive")
        if self.candidate_count <= 0:
            raise ValueError("candidate_count must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be in [0, 1]")
        if self.max_retries > 0 and not self.verifier_enabled:
            raise ValueError("retries require verifier_enabled to decide when to retry")
        if self.meta_verifier_enabled and not self.verifier_enabled:
            raise ValueError("meta_verifier_enabled requires verifier_enabled")

    def to_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        raw["retrieval_mode"] = self.retrieval_mode.value
        raw["context_policy"] = self.context_policy.value
        raw["instruction_mode"] = self.instruction_mode.value
        return raw

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "HarnessConfig":
        return cls(**raw)


@dataclass(slots=True)
class ConfigMatrix:
    """A named set of harness configs to run against the same benchmark."""

    label: str
    configs: list[HarnessConfig] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"label": self.label, "configs": [c.to_dict() for c in self.configs]}


def load_config(path: str | Path) -> HarnessConfig:
    return HarnessConfig.from_dict(json.loads(Path(path).read_text()))


def load_matrix(path: str | Path) -> ConfigMatrix:
    raw = json.loads(Path(path).read_text())
    return ConfigMatrix(
        label=raw["label"],
        configs=[HarnessConfig.from_dict(c) for c in raw["configs"]],
    )
