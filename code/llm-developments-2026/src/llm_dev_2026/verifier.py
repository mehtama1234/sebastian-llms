from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .model import Attempt


@dataclass(slots=True)
class VerifierOutcome:
    accepted: bool
    confidence: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"accepted": self.accepted, "confidence": self.confidence, "reason": self.reason}


def verify(attempt: Attempt) -> VerifierOutcome:
    """Grounding check: did the evidence the model cites actually reach the context?

    This simulated verifier is a near-oracle grounding checker, so the verifier
    lift it reports is an *upper bound* — a real verifier is imperfect and would
    recover less. What is reusable regardless is the harness mechanic: reject
    ungrounded claims, retry, and escalate instead of shipping a bluff.
    """
    if attempt.grounded:
        return VerifierOutcome(accepted=True, confidence=1.0, reason="grounded")
    return VerifierOutcome(accepted=False, confidence=0.0, reason=f"ungrounded:{attempt.stage}")
