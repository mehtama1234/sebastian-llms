from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import ConfigMatrix, ContextPolicy, HarnessConfig, InstructionMode, RetrievalMode
from .corpus import Benchmark, build_default_benchmark
from .harness import run_config
from .scorecard import Scorecard, ScorecardDelta, build_scorecard, compare_scorecards

BASELINE = "baseline"
VERIFIER_ON = "verifier_on"
PRODUCTION = "production_candidate"


def default_matrix() -> ConfigMatrix:
    """A config matrix where each variant isolates one production question.

    Every variant changes exactly one axis from ``baseline`` (or from
    ``verifier_on`` for the test-time-scaling axis, since candidate selection needs
    a verifier). ``production_candidate`` combines the axis winners so the sweep
    ends with a single adopt-or-not recommendation.
    """
    baseline = HarnessConfig(BASELINE)  # lexical, inline_full, none, 1 attempt, no verifier
    return ConfigMatrix(
        label="llm-developments-2026-default",
        configs=[
            baseline,
            # Retrieval axis (Is Grep All You Need? / hybrid search).
            HarnessConfig("retrieval_vector", retrieval_mode=RetrievalMode.VECTOR),
            HarnessConfig("retrieval_hybrid", retrieval_mode=RetrievalMode.HYBRID),
            HarnessConfig("retrieval_sparse", retrieval_mode=RetrievalMode.SPARSE),
            # Context-delivery axis (inline vs pointer, context pressure).
            HarnessConfig("context_snippet", context_policy=ContextPolicy.INLINE_SNIPPET),
            HarnessConfig("context_pointer", context_policy=ContextPolicy.POINTER),
            # Repo-instruction axis (Evaluating AGENTS.md).
            HarnessConfig("instructions_root", instruction_mode=InstructionMode.ROOT),
            HarnessConfig("instructions_hierarchical", instruction_mode=InstructionMode.HIERARCHICAL),
            # Verifier axis (Learning to Self-Verify).
            HarnessConfig(VERIFIER_ON, verifier_enabled=True),
            HarnessConfig("meta_verifier_on", verifier_enabled=True, meta_verifier_enabled=True),
            # Test-time scaling axis (PaCoRe / Share More, Search Less), all with verifier.
            HarnessConfig("attempts_multi", verifier_enabled=True, candidate_count=3),
            HarnessConfig("attempts_shared", verifier_enabled=True, candidate_count=3, share_evidence=True),
            HarnessConfig("attempts_retry", verifier_enabled=True, max_retries=3),
            # Combined production candidate: the axis winners stacked together.
            HarnessConfig(
                PRODUCTION,
                retrieval_mode=RetrievalMode.HYBRID,
                context_policy=ContextPolicy.INLINE_FULL,
                instruction_mode=InstructionMode.HIERARCHICAL,
                verifier_enabled=True,
                candidate_count=3,
                share_evidence=True,
                max_retries=2,
            ),
        ],
    )


# Which comparisons the memo reasons about: (baseline_name, candidate_name, axis).
COMPARISON_PLAN: list[tuple[str, str, str]] = [
    (BASELINE, "retrieval_vector", "retrieval"),
    (BASELINE, "retrieval_hybrid", "retrieval"),
    (BASELINE, "retrieval_sparse", "retrieval"),
    (BASELINE, "context_snippet", "context"),
    (BASELINE, "context_pointer", "context"),
    (BASELINE, "instructions_root", "instructions"),
    (BASELINE, "instructions_hierarchical", "instructions"),
    (BASELINE, VERIFIER_ON, "verifier"),
    (VERIFIER_ON, "meta_verifier_on", "verifier"),
    (VERIFIER_ON, "attempts_multi", "test_time_scaling"),
    (VERIFIER_ON, "attempts_shared", "test_time_scaling"),
    (VERIFIER_ON, "attempts_retry", "test_time_scaling"),
    (BASELINE, PRODUCTION, "combined"),
]


@dataclass(slots=True)
class ExperimentReport:
    label: str
    scorecards: dict[str, Scorecard]
    comparisons: list[ScorecardDelta]
    comparison_axis: dict[str, str] = field(default_factory=dict)  # "base->cand" -> axis

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "scorecards": {name: sc.to_dict() for name, sc in self.scorecards.items()},
            "comparisons": [c.to_dict() for c in self.comparisons],
            "comparison_axis": self.comparison_axis,
        }


def run_experiment(bench: Benchmark | None = None, matrix: ConfigMatrix | None = None) -> ExperimentReport:
    bench = bench or build_default_benchmark()
    matrix = matrix or default_matrix()
    scorecards: dict[str, Scorecard] = {}
    for config in matrix.configs:
        runs = run_config(bench, config)
        scorecards[config.name] = build_scorecard(config.name, runs)

    comparisons: list[ScorecardDelta] = []
    axis_map: dict[str, str] = {}
    for base, cand, axis in COMPARISON_PLAN:
        if base in scorecards and cand in scorecards:
            delta = compare_scorecards(scorecards[base], scorecards[cand])
            comparisons.append(delta)
            axis_map[f"{base}->{cand}"] = axis
    return ExperimentReport(
        label=matrix.label,
        scorecards=scorecards,
        comparisons=comparisons,
        comparison_axis=axis_map,
    )
