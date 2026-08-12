from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any

from .benchmark_schema import BenchmarkManifest, RealTask
from .meta_verifier import MetaVerifierOutcome, meta_verify
from .model import Attempt
from .runtime import RuntimeAttemptArtifact, run_real_task
from .provider import AttemptProvider
from .verifier import VerifierOutcome, verify
from .config import InstructionMode

_VALIDATION_CACHE: dict[tuple[str, str, tuple[str, ...], tuple[int, ...]], list[dict[str, Any]]] = {}


@dataclass(slots=True)
class ValidationCommandResult:
    command: str
    exit_code: int
    passed: bool
    stdout: str
    stderr: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "passed": self.passed,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


@dataclass(slots=True)
class RealTaskVerificationArtifact:
    task_id: str
    runtime: dict[str, Any]
    verifier: dict[str, Any]
    meta_verifier: dict[str, Any]
    validation_results: list[dict[str, Any]]
    accepted: bool
    escalated: bool
    final_stage: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "runtime": self.runtime,
            "verifier": self.verifier,
            "meta_verifier": self.meta_verifier,
            "validation_results": self.validation_results,
            "accepted": self.accepted,
            "escalated": self.escalated,
            "final_stage": self.final_stage,
        }


def _truncate(text: str, limit: int = 1200) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def run_validation(task: RealTask, repo_root: str) -> list[ValidationCommandResult]:
    cache_key = (
        task.task_id,
        repo_root,
        tuple(task.validation.commands),
        tuple(task.validation.expected_exit_codes),
    )
    cached = _VALIDATION_CACHE.get(cache_key)
    if cached is not None:
        return [ValidationCommandResult(**item) for item in cached]

    results: list[ValidationCommandResult] = []
    for command in task.validation.commands:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            shell=True,
            text=True,
            capture_output=True,
        )
        results.append(
            ValidationCommandResult(
                command=command,
                exit_code=completed.returncode,
                passed=completed.returncode in task.validation.expected_exit_codes,
                stdout=_truncate(completed.stdout),
                stderr=_truncate(completed.stderr),
            )
        )
    _VALIDATION_CACHE[cache_key] = [result.to_dict() for result in results]
    return results


def _stage_for_artifact(
    artifact: RuntimeAttemptArtifact,
    *,
    provider_grounded: bool,
    validation_passed: bool,
) -> str:
    if artifact.missing_paths:
        return "missing_paths"
    if not provider_grounded:
        return "runtime_ungrounded"
    if not validation_passed:
        return "validation_failed"
    return "ok"


def _artifact_to_attempt(
    artifact: RuntimeAttemptArtifact,
    *,
    validation_passed: bool,
) -> Attempt:
    provider_grounded = bool(artifact.response.get("grounded"))
    stage = _stage_for_artifact(
        artifact,
        provider_grounded=provider_grounded,
        validation_passed=validation_passed,
    )
    context_snippets = artifact.request.get("context_snippets", [])
    gold_files = set(artifact.request.get("gold_files", []))
    gold_retrieved = any(snippet.get("path") in gold_files for snippet in context_snippets)
    prompt_tokens = artifact.request.get("instruction_tokens", 0)
    prompt_tokens += sum(len(snippet.get("text", "").split()) for snippet in context_snippets)
    effective_grounded = provider_grounded and gold_retrieved and validation_passed and not artifact.missing_paths
    return Attempt(
        seed=0,
        doc_ids=list(artifact.request.get("gold_files", [])),
        gold_retrieved=gold_retrieved,
        claimed_success=bool(artifact.response.get("output_text", "").strip()),
        grounded=effective_grounded,
        stage=stage,
        prompt_tokens=prompt_tokens,
        retrieval_ops=len(context_snippets),
    )


def verify_real_task_artifact(
    task: RealTask,
    artifact: RuntimeAttemptArtifact,
    *,
    threshold: float = 0.5,
    run_validation_checks: bool = True,
) -> RealTaskVerificationArtifact:
    validation_results = run_validation(task, artifact.repo_root) if run_validation_checks else []
    validation_passed = all(result.passed for result in validation_results) if validation_results else True
    attempt = _artifact_to_attempt(artifact, validation_passed=validation_passed)
    verdict: VerifierOutcome = verify(attempt, threshold=threshold)
    meta: MetaVerifierOutcome = meta_verify(attempt, verdict, threshold=threshold)
    accepted = meta.accepted
    return RealTaskVerificationArtifact(
        task_id=task.task_id,
        runtime=artifact.to_dict(),
        verifier=verdict.to_dict(),
        meta_verifier=meta.to_dict(),
        validation_results=[result.to_dict() for result in validation_results],
        accepted=accepted,
        escalated=not accepted,
        final_stage=attempt.stage,
    )


def run_real_task_with_verifier(
    manifest: BenchmarkManifest,
    task_id: str,
    provider: AttemptProvider,
    *,
    instruction_mode: InstructionMode = InstructionMode.NONE,
    evidence_source: str = "gold",
    retrieval_mode: str = "task_aware",
    retrieval_top_k: int = 2,
    evidence_selection: str = "all",
    evidence_top_k: int = 1,
    threshold: float = 0.5,
    run_validation_checks: bool = True,
) -> RealTaskVerificationArtifact:
    task = next(task for task in manifest.tasks if task.task_id == task_id)
    artifact = run_real_task(
        manifest,
        task_id,
        provider,
        instruction_mode=instruction_mode,
        evidence_source=evidence_source,
        retrieval_mode=retrieval_mode,
        retrieval_top_k=retrieval_top_k,
        evidence_selection=evidence_selection,
        evidence_top_k=evidence_top_k,
    )
    return verify_real_task_artifact(
        task,
        artifact,
        threshold=threshold,
        run_validation_checks=run_validation_checks,
    )
