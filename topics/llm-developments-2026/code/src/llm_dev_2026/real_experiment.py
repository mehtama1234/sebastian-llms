from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .benchmark_loader import load_benchmark_manifest
from .config import InstructionMode
from .provider import AttemptProvider, build_provider
from .real_scorecard import RealTaskScorecard, build_real_task_scorecard
from .real_task_verifier import RealTaskVerificationArtifact, run_real_task_with_verifier
from .task_pack import TaskPack


@dataclass(slots=True)
class RealExperimentReport:
    benchmark_id: str
    version: str
    provider_backend: str
    task_count: int
    scorecard: RealTaskScorecard
    tasks: list[RealTaskVerificationArtifact]

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "version": self.version,
            "provider_backend": self.provider_backend,
            "task_count": self.task_count,
            "scorecard": self.scorecard.to_dict(),
            "tasks": [artifact.to_dict() for artifact in self.tasks],
        }


def run_real_experiment(
    manifest_path: str,
    *,
    provider_backend: str = "local",
    model: str = "gpt-5.6",
    api_key_env: str = "OPENAI_API_KEY",
    instruction_mode: InstructionMode = InstructionMode.NONE,
    evidence_source: str = "gold",
    retrieval_mode: str = "task_aware",
    retrieval_top_k: int = 2,
    evidence_selection: str = "all",
    evidence_top_k: int = 1,
    run_validation_checks: bool = True,
    task_class: str | None = None,
    difficulty: str | None = None,
    long_context: bool | None = None,
) -> RealExperimentReport:
    manifest = load_benchmark_manifest(manifest_path)
    pack = TaskPack(manifest)
    tasks = pack.slice(task_class=task_class, difficulty=difficulty, long_context=long_context)
    provider: AttemptProvider = build_provider(provider_backend, model=model, api_key_env=api_key_env)
    artifacts = [
        run_real_task_with_verifier(
            manifest,
            task.task_id,
            provider,
            instruction_mode=instruction_mode,
            evidence_source=evidence_source,
            retrieval_mode=retrieval_mode,
            retrieval_top_k=retrieval_top_k,
            evidence_selection=evidence_selection,
            evidence_top_k=evidence_top_k,
            run_validation_checks=run_validation_checks,
        )
        for task in tasks
    ]
    scorecard = build_real_task_scorecard(
        f"{manifest.benchmark_id}:{provider_backend}:{evidence_source}:{retrieval_mode}:{evidence_selection}",
        artifacts,
    )
    return RealExperimentReport(
        benchmark_id=manifest.benchmark_id,
        version=manifest.version,
        provider_backend=provider_backend,
        task_count=len(artifacts),
        scorecard=scorecard,
        tasks=artifacts,
    )
