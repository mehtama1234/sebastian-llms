from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from .harness import ScenarioRun
from .model import STAGE_OK


def _rate(values: list[bool]) -> float:
    return sum(values) / len(values) if values else 0.0


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


@dataclass(slots=True)
class Scorecard:
    """Production-style scorecard for one harness config over the benchmark."""

    config_name: str
    scenario_count: int
    task_success_rate: float  # grounded, honest success
    reported_success_rate: float  # what the harness claimed
    hallucination_rate: float  # claimed success that was not grounded
    escalation_rate: float
    gold_retrieval_rate: float
    mean_prompt_tokens_final: float
    mean_prompt_tokens_total: float
    mean_retrieval_ops: float
    mean_latency_units: float
    mean_attempts: float
    success_by_task_class: dict[str, float]
    failure_stage_breakdown: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__slots__}


def build_scorecard(config_name: str, runs: list[ScenarioRun]) -> Scorecard:
    by_class: dict[str, list[bool]] = {}
    for r in runs:
        by_class.setdefault(r.task_class, []).append(r.true_success)
    stage_counts: Counter[str] = Counter(r.final_stage for r in runs if r.final_stage != STAGE_OK)
    return Scorecard(
        config_name=config_name,
        scenario_count=len(runs),
        task_success_rate=_rate([r.true_success for r in runs]),
        reported_success_rate=_rate([r.reported_success for r in runs]),
        hallucination_rate=_rate([r.hallucinated for r in runs]),
        escalation_rate=_rate([r.escalated for r in runs]),
        gold_retrieval_rate=_rate([r.gold_retrieved for r in runs]),
        mean_prompt_tokens_final=_mean([r.prompt_tokens_final for r in runs]),
        mean_prompt_tokens_total=_mean([r.prompt_tokens_total for r in runs]),
        mean_retrieval_ops=_mean([r.retrieval_ops_total for r in runs]),
        mean_latency_units=_mean([r.latency_units for r in runs]),
        mean_attempts=_mean([r.attempts_used for r in runs]),
        success_by_task_class={k: _rate(v) for k, v in sorted(by_class.items())},
        failure_stage_breakdown=dict(sorted(stage_counts.items())),
    )


@dataclass(slots=True)
class ScorecardDelta:
    """Directional comparison of a candidate config against a baseline."""

    baseline: str
    candidate: str
    task_success_delta: float
    hallucination_delta: float
    prompt_tokens_final_delta: float
    retrieval_ops_delta: float
    latency_delta: float
    verdict: str  # improved | regressed | mixed | neutral

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__slots__}


def compare_scorecards(baseline: Scorecard, candidate: Scorecard) -> ScorecardDelta:
    """Compare two scorecards on the axes that decide production-worthiness.

    A candidate "improves" only if it raises honest success or cuts hallucination
    without a meaningful quality loss; a pure cost increase with no quality gain is
    a regression. This mirrors the arch-advances lane's decision-stack discipline:
    numbers drive the verdict, not intuition.
    """
    success_delta = candidate.task_success_rate - baseline.task_success_rate
    halluc_delta = candidate.hallucination_rate - baseline.hallucination_rate
    tokens_delta = candidate.mean_prompt_tokens_final - baseline.mean_prompt_tokens_final
    ops_delta = candidate.mean_retrieval_ops - baseline.mean_retrieval_ops
    latency_delta = candidate.mean_latency_units - baseline.mean_latency_units

    quality_up = success_delta > 1e-9 or halluc_delta < -1e-9
    quality_down = success_delta < -1e-9 or halluc_delta > 1e-9
    cost_up = latency_delta > 1e-9

    if quality_up and not quality_down:
        verdict = "improved"
    elif quality_down and not quality_up:
        verdict = "regressed"
    elif quality_up and quality_down:
        verdict = "mixed"
    elif cost_up:
        verdict = "regressed"  # more cost, no quality gain
    else:
        verdict = "neutral"

    return ScorecardDelta(
        baseline=baseline.config_name,
        candidate=candidate.config_name,
        task_success_delta=success_delta,
        hallucination_delta=halluc_delta,
        prompt_tokens_final_delta=tokens_delta,
        retrieval_ops_delta=ops_delta,
        latency_delta=latency_delta,
        verdict=verdict,
    )
