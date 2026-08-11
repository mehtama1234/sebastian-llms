from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .model import Attempt
from .verifier import VerifierOutcome


@dataclass(slots=True)
class MetaVerifierOutcome:
    accepted: bool
    confidence: float
    reason: str
    trust_adjustment: float
    corrected_score: float
    critique: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "confidence": self.confidence,
            "reason": self.reason,
            "trust_adjustment": self.trust_adjustment,
            "corrected_score": self.corrected_score,
            "critique": self.critique,
        }


def meta_verify(
    attempt: Attempt,
    verdict: VerifierOutcome,
    *,
    threshold: float = 0.5,
) -> MetaVerifierOutcome:
    """Audit whether the verifier's judgment is internally coherent.

    The meta-verifier does not rescore from scratch. It checks whether the
    verifier's score, confidence, and critique line up with observable harness
    facts: grounding status, whether the model claimed success, and where the
    pipeline failed. That mirrors a practical meta-verifier's job: grade the
    grader, especially on polished but unsupported answers.
    """
    trust = 0.0
    notes: list[str] = []
    if verdict.accepted == attempt.grounded:
        trust += 0.35
        notes.append("decision matches grounding state")
    else:
        trust -= 0.5
        notes.append("decision disagrees with grounding state")

    if verdict.first_bad_stage == attempt.stage or (attempt.grounded and verdict.first_bad_stage is None):
        trust += 0.2
        notes.append("failure localization is coherent")
    elif not attempt.grounded:
        trust -= 0.15
        notes.append("failure localization is weak")

    if attempt.claimed_success and not attempt.grounded and "claim_without_evidence" in verdict.rubric_hits:
        trust += 0.15
        notes.append("caught unsupported success claim")
    elif attempt.claimed_success and not attempt.grounded:
        trust -= 0.1
        notes.append("missed unsupported success pattern")

    confidence_penalty = abs(verdict.confidence - (0.95 if attempt.grounded else 0.7))
    trust -= min(0.2, confidence_penalty * 0.15)

    if attempt.grounded:
        corrected_score = min(1.0, max(0.0, verdict.score + max(0.0, trust)))
    else:
        corrected_score = min(1.0, max(0.0, verdict.score - max(0.15, trust)))
    accepted = attempt.grounded and corrected_score >= threshold
    confidence = min(0.99, max(0.05, 0.65 + 0.3 * abs(trust)))
    reason = "meta_verified" if verdict.accepted == accepted else "meta_corrected"
    critique = "; ".join(notes)
    return MetaVerifierOutcome(
        accepted=accepted,
        confidence=confidence,
        reason=reason,
        trust_adjustment=trust,
        corrected_score=corrected_score,
        critique=critique,
    )
