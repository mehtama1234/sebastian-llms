from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


VALID_TASK_CLASSES = frozenset({"inspect", "diagnose", "bug_fix", "feature", "refactor", "research"})
VALID_VALIDATION_MODES = frozenset({"tests", "lint", "typecheck", "build", "diff_review", "human_review", "mixed"})
VALID_DIFFICULTIES = frozenset({"easy", "medium", "hard"})


@dataclass(slots=True)
class RepoSpec:
    repo_id: str
    root: str
    commit: str
    language: str = "unknown"
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.repo_id:
            raise ValueError("repo_id is required")
        if not self.root:
            raise ValueError("root is required")
        if not self.commit:
            raise ValueError("commit is required")

    def root_path(self) -> Path:
        return Path(self.root).expanduser()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvidenceSpan:
    path: str
    start_line: int
    end_line: int
    note: str = ""

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("evidence span path is required")
        if self.start_line <= 0:
            raise ValueError("start_line must be positive")
        if self.end_line < self.start_line:
            raise ValueError("end_line must be >= start_line")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ValidationSpec:
    mode: str
    commands: list[str] = field(default_factory=list)
    expected_exit_codes: list[int] = field(default_factory=lambda: [0])
    rubric: str = ""

    def __post_init__(self) -> None:
        if self.mode not in VALID_VALIDATION_MODES:
            raise ValueError(f"unknown validation mode: {self.mode}")
        if not self.expected_exit_codes:
            raise ValueError("expected_exit_codes cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RealTask:
    task_id: str
    repo_id: str
    repo_commit: str
    task_class: str
    prompt: str
    expected_artifact_type: str
    allowed_tools: list[str] = field(default_factory=list)
    gold_files: list[str] = field(default_factory=list)
    gold_evidence_spans: list[EvidenceSpan] = field(default_factory=list)
    validation: ValidationSpec = field(default_factory=lambda: ValidationSpec(mode="human_review"))
    difficulty: str = "medium"
    long_context: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("task_id is required")
        if not self.repo_id:
            raise ValueError("repo_id is required")
        if not self.repo_commit:
            raise ValueError("repo_commit is required")
        if self.task_class not in VALID_TASK_CLASSES:
            raise ValueError(f"unknown task_class: {self.task_class}")
        if not self.prompt:
            raise ValueError("prompt is required")
        if not self.expected_artifact_type:
            raise ValueError("expected_artifact_type is required")
        if self.difficulty not in VALID_DIFFICULTIES:
            raise ValueError(f"unknown difficulty: {self.difficulty}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "repo_id": self.repo_id,
            "repo_commit": self.repo_commit,
            "task_class": self.task_class,
            "prompt": self.prompt,
            "expected_artifact_type": self.expected_artifact_type,
            "allowed_tools": self.allowed_tools,
            "gold_files": self.gold_files,
            "gold_evidence_spans": [span.to_dict() for span in self.gold_evidence_spans],
            "validation": self.validation.to_dict(),
            "difficulty": self.difficulty,
            "long_context": self.long_context,
            "notes": self.notes,
        }


@dataclass(slots=True)
class BenchmarkManifest:
    benchmark_id: str
    version: str
    repos: list[RepoSpec]
    tasks: list[RealTask]
    description: str = ""

    def __post_init__(self) -> None:
        if not self.benchmark_id:
            raise ValueError("benchmark_id is required")
        if not self.version:
            raise ValueError("version is required")
        repo_ids = [repo.repo_id for repo in self.repos]
        if len(repo_ids) != len(set(repo_ids)):
            raise ValueError("repo ids must be unique")
        known = set(repo_ids)
        task_ids = [task.task_id for task in self.tasks]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("task ids must be unique")
        missing = sorted({task.repo_id for task in self.tasks if task.repo_id not in known})
        if missing:
            raise ValueError(f"tasks reference unknown repos: {', '.join(missing)}")

    def repo(self, repo_id: str) -> RepoSpec:
        for repo in self.repos:
            if repo.repo_id == repo_id:
                return repo
        raise KeyError(repo_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "version": self.version,
            "description": self.description,
            "repos": [repo.to_dict() for repo in self.repos],
            "tasks": [task.to_dict() for task in self.tasks],
        }


def repo_from_dict(raw: dict[str, Any]) -> RepoSpec:
    return RepoSpec(**raw)


def evidence_span_from_dict(raw: dict[str, Any]) -> EvidenceSpan:
    return EvidenceSpan(**raw)


def validation_from_dict(raw: dict[str, Any]) -> ValidationSpec:
    return ValidationSpec(**raw)


def task_from_dict(raw: dict[str, Any]) -> RealTask:
    payload = dict(raw)
    payload["gold_evidence_spans"] = [evidence_span_from_dict(item) for item in payload.get("gold_evidence_spans", [])]
    payload["validation"] = validation_from_dict(payload["validation"])
    return RealTask(**payload)


def manifest_from_dict(raw: dict[str, Any]) -> BenchmarkManifest:
    return BenchmarkManifest(
        benchmark_id=raw["benchmark_id"],
        version=raw["version"],
        description=raw.get("description", ""),
        repos=[repo_from_dict(item) for item in raw.get("repos", [])],
        tasks=[task_from_dict(item) for item in raw.get("tasks", [])],
    )
