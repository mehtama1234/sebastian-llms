from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from .real_task_verifier import RealTaskVerificationArtifact


def _rate(values: list[bool]) -> float:
    return sum(values) / len(values) if values else 0.0


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


@dataclass(slots=True)
class RealTaskScorecard:
    label: str
    task_count: int
    accepted_rate: float
    escalation_rate: float
    grounded_rate: float
    validation_pass_rate: float
    mean_prompt_tokens: float
    mean_context_snippets: float
    mean_response_tokens: float
    response_tokens_per_accepted_task: float
    success_by_task_class: dict[str, float]
    failure_stage_breakdown: dict[str, int]
    retrieval_diagnostics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {field: getattr(self, field) for field in self.__slots__}


@dataclass(slots=True)
class RealTaskScorecardDelta:
    baseline: str
    candidate: str
    accepted_delta: float
    escalation_delta: float
    grounded_delta: float
    validation_delta: float
    response_tokens_delta: float
    verdict: str

    def to_dict(self) -> dict[str, Any]:
        return {field: getattr(self, field) for field in self.__slots__}


def build_real_task_scorecard(label: str, artifacts: list[RealTaskVerificationArtifact]) -> RealTaskScorecard:
    by_class: dict[str, list[bool]] = {}
    stage_counts: Counter[str] = Counter()
    validation_success: list[bool] = []
    prompt_tokens: list[float] = []
    context_counts: list[float] = []
    response_tokens: list[float] = []
    gold_hit_flags: list[bool] = []
    gold_file_recalls: list[float] = []
    missed_gold_files: Counter[str] = Counter()

    for artifact in artifacts:
        task_class = artifact.runtime["request"]["expected_artifact_type"]
        by_class.setdefault(task_class, []).append(artifact.accepted)
        if artifact.final_stage != "ok":
            stage_counts[artifact.final_stage] += 1
        validation_success.append(all(result["passed"] for result in artifact.validation_results) if artifact.validation_results else True)
        prompt_tokens.append(float(artifact.runtime["request"]["instruction_tokens"]))
        context_counts.append(float(len(artifact.runtime["request"]["context_snippets"])))
        response_tokens.append(float(artifact.runtime["response"]["token_estimate"]))
        diagnostics = artifact.runtime.get("retrieval_diagnostics", {})
        gold_hit_flags.append(bool(diagnostics.get("has_any_gold_hit")))
        gold_file_recalls.append(float(diagnostics.get("gold_file_recall", 0.0)))
        for path in diagnostics.get("missed_gold_files", []):
            missed_gold_files[path] += 1

    accepted_total = sum(1 for artifact in artifacts if artifact.accepted)
    response_tokens_per_accepted_task = sum(response_tokens) / accepted_total if accepted_total else 0.0

    return RealTaskScorecard(
        label=label,
        task_count=len(artifacts),
        accepted_rate=_rate([artifact.accepted for artifact in artifacts]),
        escalation_rate=_rate([artifact.escalated for artifact in artifacts]),
        grounded_rate=_rate([bool(artifact.runtime["response"]["grounded"]) for artifact in artifacts]),
        validation_pass_rate=_rate(validation_success),
        mean_prompt_tokens=_mean(prompt_tokens),
        mean_context_snippets=_mean(context_counts),
        mean_response_tokens=_mean(response_tokens),
        response_tokens_per_accepted_task=response_tokens_per_accepted_task,
        success_by_task_class={name: _rate(values) for name, values in sorted(by_class.items())},
        failure_stage_breakdown=dict(sorted(stage_counts.items())),
        retrieval_diagnostics={
            "task_with_any_gold_hit_rate": _rate(gold_hit_flags),
            "mean_gold_file_recall": _mean(gold_file_recalls),
            "tasks_without_gold_hit": sum(1 for hit in gold_hit_flags if not hit),
            "top_missed_gold_files": [
                {"path": path, "count": count}
                for path, count in missed_gold_files.most_common(5)
            ],
        },
    )


def compare_real_task_scorecards(
    baseline: RealTaskScorecard,
    candidate: RealTaskScorecard,
    *,
    baseline_name: str | None = None,
    candidate_name: str | None = None,
) -> RealTaskScorecardDelta:
    accepted_delta = candidate.accepted_rate - baseline.accepted_rate
    escalation_delta = candidate.escalation_rate - baseline.escalation_rate
    grounded_delta = candidate.grounded_rate - baseline.grounded_rate
    validation_delta = candidate.validation_pass_rate - baseline.validation_pass_rate
    response_tokens_delta = candidate.mean_response_tokens - baseline.mean_response_tokens

    quality_up = accepted_delta > 1e-9 or grounded_delta > 1e-9 or escalation_delta < -1e-9
    quality_down = accepted_delta < -1e-9 or grounded_delta < -1e-9 or escalation_delta > 1e-9
    cost_up = response_tokens_delta > 1e-9

    if quality_up and not quality_down:
        verdict = "improved"
    elif quality_down and not quality_up:
        verdict = "regressed"
    elif quality_up and quality_down:
        verdict = "mixed"
    elif cost_up:
        verdict = "regressed"
    else:
        verdict = "neutral"

    return RealTaskScorecardDelta(
        baseline=baseline_name or baseline.label,
        candidate=candidate_name or candidate.label,
        accepted_delta=accepted_delta,
        escalation_delta=escalation_delta,
        grounded_delta=grounded_delta,
        validation_delta=validation_delta,
        response_tokens_delta=response_tokens_delta,
        verdict=verdict,
    )
