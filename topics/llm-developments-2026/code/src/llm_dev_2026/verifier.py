from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .model import Attempt


@dataclass(slots=True)
class VerifierOutcome:
    accepted: bool
    confidence: float
    reason: str
    score: float
    first_bad_stage: str | None
    critique: str
    rubric_hits: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "confidence": self.confidence,
            "reason": self.reason,
            "score": self.score,
            "first_bad_stage": self.first_bad_stage,
            "critique": self.critique,
            "rubric_hits": self.rubric_hits,
        }


def verify(attempt: Attempt, *, threshold: float = 0.5) -> VerifierOutcome:
    """Grounding-oriented verifier with structured feedback.

    This simulated verifier is a near-oracle grounding checker, so the verifier
    lift it reports is an *upper bound* — a real verifier is imperfect and would
    recover less. What is reusable regardless is the harness mechanic: reject
    ungrounded claims, retry, and escalate instead of shipping a bluff.
    """
    if attempt.grounded:
        return VerifierOutcome(
            accepted=True,
            confidence=0.98,
            reason="grounded",
            score=1.0,
            first_bad_stage=None,
            critique="Evidence reached context and the answer can be backed by the retrieved material.",
            rubric_hits=["evidence_present", "retrieval_support", "claim_grounded"],
        )

    if not attempt.claimed_success:
        return VerifierOutcome(
            accepted=False,
            confidence=0.92,
            reason=f"incomplete:{attempt.stage}",
            score=0.15,
            first_bad_stage=attempt.stage,
            critique="The attempt did not produce a supported answer, so it should be retried or escalated.",
            rubric_hits=["answer_missing"],
        )

    score_map = {
        "retrieval_miss": 0.18,
        "recall_flaky": 0.32,
        "context_drop": 0.28,
        "missing_guidance": 0.12,
    }
    score = score_map.get(attempt.stage, 0.2)
    confidence = 0.55 + min(0.35, 0.04 * len(attempt.doc_ids))
    accepted = score >= threshold and attempt.grounded
    return VerifierOutcome(
        accepted=accepted,
        confidence=confidence,
        reason=f"ungrounded:{attempt.stage}",
        score=score,
        first_bad_stage=attempt.stage,
        critique=(
            "The answer sounds complete, but the supporting evidence never reached the final context. "
            f"Failure point: {attempt.stage}."
        ),
        rubric_hits=["claim_without_evidence", f"stage:{attempt.stage}"],
    )
