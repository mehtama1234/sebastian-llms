from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .benchmark_schema import BenchmarkManifest, RealTask


@dataclass(slots=True)
class TaskReadiness:
    task_id: str
    repo_id: str
    repo_root: str
    repo_exists: bool
    gold_files_present: list[str] = field(default_factory=list)
    missing_gold_files: list[str] = field(default_factory=list)
    evidence_paths_present: list[str] = field(default_factory=list)
    missing_evidence_paths: list[str] = field(default_factory=list)
    validation_mode: str = ""
    command_count: int = 0
    allowed_tools: list[str] = field(default_factory=list)
    long_context: bool = False
    ready: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "repo_id": self.repo_id,
            "repo_root": self.repo_root,
            "repo_exists": self.repo_exists,
            "gold_files_present": self.gold_files_present,
            "missing_gold_files": self.missing_gold_files,
            "evidence_paths_present": self.evidence_paths_present,
            "missing_evidence_paths": self.missing_evidence_paths,
            "validation_mode": self.validation_mode,
            "command_count": self.command_count,
            "allowed_tools": self.allowed_tools,
            "long_context": self.long_context,
            "ready": self.ready,
            "notes": self.notes,
        }


@dataclass(slots=True)
class RealBenchmarkRuntimeReport:
    benchmark_id: str
    version: str
    task_count: int
    ready_task_count: int
    repos_missing: list[str]
    tasks: list[TaskReadiness]

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "version": self.version,
            "task_count": self.task_count,
            "ready_task_count": self.ready_task_count,
            "repos_missing": self.repos_missing,
            "tasks": [task.to_dict() for task in self.tasks],
        }


def _task_readiness(manifest: BenchmarkManifest, task: RealTask) -> TaskReadiness:
    repo = manifest.repo(task.repo_id)
    repo_root = repo.root_path()
    repo_exists = repo_root.exists()

    gold_files_present: list[str] = []
    missing_gold_files: list[str] = []
    for rel_path in task.gold_files:
        candidate = repo_root / rel_path
        if candidate.exists():
            gold_files_present.append(rel_path)
        else:
            missing_gold_files.append(rel_path)

    evidence_paths_present: list[str] = []
    missing_evidence_paths: list[str] = []
    for span in task.gold_evidence_spans:
        candidate = repo_root / span.path
        if candidate.exists():
            evidence_paths_present.append(span.path)
        else:
            missing_evidence_paths.append(span.path)

    notes: list[str] = []
    if repo_exists:
        notes.append("repo_root_present")
    else:
        notes.append("repo_root_missing")
    if task.validation.commands:
        notes.append("has_validation_commands")
    if task.long_context:
        notes.append("long_context_task")
    if task.validation.mode in {"human_review", "diff_review"}:
        notes.append("needs_review_loop")

    ready = repo_exists and not missing_gold_files and not missing_evidence_paths
    return TaskReadiness(
        task_id=task.task_id,
        repo_id=task.repo_id,
        repo_root=str(repo_root),
        repo_exists=repo_exists,
        gold_files_present=gold_files_present,
        missing_gold_files=missing_gold_files,
        evidence_paths_present=evidence_paths_present,
        missing_evidence_paths=missing_evidence_paths,
        validation_mode=task.validation.mode,
        command_count=len(task.validation.commands),
        allowed_tools=task.allowed_tools,
        long_context=task.long_context,
        ready=ready,
        notes=notes,
    )


def run_real_benchmark_readiness(manifest: BenchmarkManifest) -> RealBenchmarkRuntimeReport:
    tasks = [_task_readiness(manifest, task) for task in manifest.tasks]
    repos_missing = sorted({task.repo_root for task in tasks if not task.repo_exists})
    return RealBenchmarkRuntimeReport(
        benchmark_id=manifest.benchmark_id,
        version=manifest.version,
        task_count=len(tasks),
        ready_task_count=sum(task.ready for task in tasks),
        repos_missing=repos_missing,
        tasks=tasks,
    )


def format_real_benchmark_summary(report: RealBenchmarkRuntimeReport) -> str:
    header = (
        f"benchmark={report.benchmark_id} version={report.version} "
        f"ready={report.ready_task_count}/{report.task_count}"
    )
    rows = [header, ""]
    for task in report.tasks:
        rows.append(
            f"{task.task_id:<46} ready={str(task.ready).lower():<5} "
            f"repo={str(task.repo_exists).lower():<5} "
            f"gold_missing={len(task.missing_gold_files):<2} "
            f"evidence_missing={len(task.missing_evidence_paths):<2} "
            f"validation={task.validation_mode}"
        )
    if report.repos_missing:
        rows.extend(["", "missing repo roots:"])
        rows.extend(f"  - {path}" for path in report.repos_missing)
    return "\n".join(rows)
