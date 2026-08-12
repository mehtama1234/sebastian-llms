from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import InstructionMode
from .real_experiment import RealExperimentReport, run_real_experiment
from .real_scorecard import RealTaskScorecard, RealTaskScorecardDelta, compare_real_task_scorecards


@dataclass(slots=True)
class RealPolicyConfig:
    name: str
    provider_backend: str = "local"
    instruction_mode: InstructionMode = InstructionMode.NONE
    evidence_source: str = "gold"
    retrieval_mode: str = "task_aware"
    retrieval_top_k: int = 2
    evidence_selection: str = "all"
    evidence_top_k: int = 1
    run_validation_checks: bool = True

    def __post_init__(self) -> None:
        self.instruction_mode = InstructionMode(self.instruction_mode)
        if self.evidence_source not in {"gold", "retrieval"}:
            raise ValueError(f"unknown evidence_source: {self.evidence_source}")
        if self.retrieval_mode not in {"lexical", "sparse", "task_aware"}:
            raise ValueError(f"unknown retrieval_mode: {self.retrieval_mode}")
        if self.retrieval_top_k <= 0:
            raise ValueError("retrieval_top_k must be positive")
        if self.evidence_selection not in {"all", "first", "sparse"}:
            raise ValueError(f"unknown evidence_selection: {self.evidence_selection}")
        if self.evidence_top_k <= 0:
            raise ValueError("evidence_top_k must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "provider_backend": self.provider_backend,
            "instruction_mode": self.instruction_mode.value,
            "evidence_source": self.evidence_source,
            "retrieval_mode": self.retrieval_mode,
            "retrieval_top_k": self.retrieval_top_k,
            "evidence_selection": self.evidence_selection,
            "evidence_top_k": self.evidence_top_k,
            "run_validation_checks": self.run_validation_checks,
        }


@dataclass(slots=True)
class RealPolicyMatrix:
    label: str
    configs: list[RealPolicyConfig]


REAL_BASELINE = "real_baseline"


def default_real_policy_matrix() -> RealPolicyMatrix:
    return RealPolicyMatrix(
        label="llm-developments-2026-real-policy-default",
        configs=[
            RealPolicyConfig(REAL_BASELINE, provider_backend="local", instruction_mode=InstructionMode.NONE, evidence_source="gold", evidence_selection="all", run_validation_checks=True),
            RealPolicyConfig("real_instructions_root", provider_backend="local", instruction_mode=InstructionMode.ROOT, evidence_source="gold", evidence_selection="all", run_validation_checks=True),
            RealPolicyConfig("real_instructions_hierarchical", provider_backend="local", instruction_mode=InstructionMode.HIERARCHICAL, evidence_source="gold", evidence_selection="all", run_validation_checks=True),
            RealPolicyConfig("real_evidence_first", provider_backend="local", instruction_mode=InstructionMode.NONE, evidence_source="gold", evidence_selection="first", run_validation_checks=True),
            RealPolicyConfig("real_evidence_sparse", provider_backend="local", instruction_mode=InstructionMode.NONE, evidence_source="gold", evidence_selection="sparse", evidence_top_k=1, run_validation_checks=True),
            RealPolicyConfig("real_retrieval_lexical", provider_backend="local", instruction_mode=InstructionMode.NONE, evidence_source="retrieval", retrieval_mode="lexical", retrieval_top_k=2, run_validation_checks=True),
            RealPolicyConfig("real_retrieval_sparse", provider_backend="local", instruction_mode=InstructionMode.NONE, evidence_source="retrieval", retrieval_mode="sparse", retrieval_top_k=2, run_validation_checks=True),
            RealPolicyConfig("real_retrieval_task_aware", provider_backend="local", instruction_mode=InstructionMode.NONE, evidence_source="retrieval", retrieval_mode="task_aware", retrieval_top_k=2, run_validation_checks=True),
            RealPolicyConfig("real_skip_validation", provider_backend="local", instruction_mode=InstructionMode.NONE, evidence_source="gold", evidence_selection="all", run_validation_checks=False),
        ],
    )


def retrieval_only_real_policy_matrix(*, run_validation_checks: bool = True) -> RealPolicyMatrix:
    return RealPolicyMatrix(
        label="llm-developments-2026-real-policy-retrieval",
        configs=[
            RealPolicyConfig("real_retrieval_lexical", provider_backend="local", instruction_mode=InstructionMode.NONE, evidence_source="retrieval", retrieval_mode="lexical", retrieval_top_k=2, run_validation_checks=run_validation_checks),
            RealPolicyConfig("real_retrieval_sparse", provider_backend="local", instruction_mode=InstructionMode.NONE, evidence_source="retrieval", retrieval_mode="sparse", retrieval_top_k=2, run_validation_checks=run_validation_checks),
            RealPolicyConfig("real_retrieval_task_aware", provider_backend="local", instruction_mode=InstructionMode.NONE, evidence_source="retrieval", retrieval_mode="task_aware", retrieval_top_k=2, run_validation_checks=run_validation_checks),
        ],
    )


REAL_COMPARISON_PLAN: list[tuple[str, str, str]] = [
    (REAL_BASELINE, "real_instructions_root", "instructions"),
    (REAL_BASELINE, "real_instructions_hierarchical", "instructions"),
    (REAL_BASELINE, "real_evidence_first", "retrieval"),
    (REAL_BASELINE, "real_evidence_sparse", "retrieval"),
    (REAL_BASELINE, "real_retrieval_lexical", "retrieval"),
    (REAL_BASELINE, "real_retrieval_sparse", "retrieval"),
    (REAL_BASELINE, "real_retrieval_task_aware", "retrieval"),
    (REAL_BASELINE, "real_skip_validation", "validation"),
]


@dataclass(slots=True)
class RealPolicyExperimentReport:
    label: str
    reports: dict[str, RealExperimentReport]
    scorecards: dict[str, RealTaskScorecard]
    comparisons: list[RealTaskScorecardDelta]
    comparison_axis: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "reports": {name: report.to_dict() for name, report in self.reports.items()},
            "scorecards": {name: scorecard.to_dict() for name, scorecard in self.scorecards.items()},
            "comparisons": [comparison.to_dict() for comparison in self.comparisons],
            "comparison_axis": self.comparison_axis,
        }


def run_real_policy_experiment(
    manifest_path: str,
    *,
    matrix: RealPolicyMatrix | None = None,
    task_class: str | None = None,
    difficulty: str | None = None,
    long_context: bool | None = None,
) -> RealPolicyExperimentReport:
    matrix = matrix or default_real_policy_matrix()
    reports: dict[str, RealExperimentReport] = {}
    scorecards: dict[str, RealTaskScorecard] = {}
    for config in matrix.configs:
        report = run_real_experiment(
            manifest_path,
            provider_backend=config.provider_backend,
            instruction_mode=config.instruction_mode,
            evidence_source=config.evidence_source,
            retrieval_mode=config.retrieval_mode,
            retrieval_top_k=config.retrieval_top_k,
            evidence_selection=config.evidence_selection,
            evidence_top_k=config.evidence_top_k,
            run_validation_checks=config.run_validation_checks,
            task_class=task_class,
            difficulty=difficulty,
            long_context=long_context,
        )
        reports[config.name] = report
        scorecards[config.name] = report.scorecard

    comparisons: list[RealTaskScorecardDelta] = []
    axis_map: dict[str, str] = {}
    for base, cand, axis in REAL_COMPARISON_PLAN:
        if base in scorecards and cand in scorecards:
            comparison = compare_real_task_scorecards(
                scorecards[base],
                scorecards[cand],
                baseline_name=base,
                candidate_name=cand,
            )
            comparisons.append(comparison)
            axis_map[f"{base}->{cand}"] = axis
    return RealPolicyExperimentReport(
        label=matrix.label,
        reports=reports,
        scorecards=scorecards,
        comparisons=comparisons,
        comparison_axis=axis_map,
    )
