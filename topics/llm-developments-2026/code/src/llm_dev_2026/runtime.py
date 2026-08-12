from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .benchmark_schema import BenchmarkManifest, RealTask
from .config import InstructionMode
from .instructions import InstructionLoad, load_instructions
from .provider import AttemptProvider, EvidenceSnippet, ProviderRequest, ProviderResponse
from .real_retrieval import retrieve_repo_chunks
from .text import tokenize


@dataclass(slots=True)
class RuntimeAttemptArtifact:
    task_id: str
    repo_id: str
    repo_root: str
    instruction: dict[str, Any]
    request: dict[str, Any]
    response: dict[str, Any]
    retrieval_diagnostics: dict[str, Any]
    ready: bool
    missing_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "repo_id": self.repo_id,
            "repo_root": self.repo_root,
            "instruction": self.instruction,
            "request": self.request,
            "response": self.response,
            "retrieval_diagnostics": self.retrieval_diagnostics,
            "ready": self.ready,
            "missing_paths": self.missing_paths,
        }


VALID_EVIDENCE_SELECTIONS = frozenset({"all", "first", "sparse"})
VALID_EVIDENCE_SOURCES = frozenset({"gold", "retrieval"})
VALID_RETRIEVAL_MODES = frozenset({"lexical", "sparse", "task_aware"})


def _repo_area(task: RealTask) -> str:
    if task.gold_files:
        first = Path(task.gold_files[0])
        if len(first.parts) >= 2:
            return first.parts[0]
    return "generic"


def _read_lines(path: Path, start_line: int, end_line: int) -> str:
    lines = path.read_text().splitlines()
    start = max(0, start_line - 1)
    end = min(len(lines), end_line)
    return "\n".join(lines[start:end])


def _snippet_score(prompt: str, snippet: EvidenceSnippet) -> float:
    query_tokens = set(tokenize(prompt))
    snippet_tokens = tokenize(snippet.text)
    overlap = sum(1 for token in snippet_tokens if token in query_tokens)
    path_bonus = sum(1 for token in tokenize(snippet.path) if token in query_tokens)
    return float(overlap + 0.5 * path_bonus)


def _select_snippets(
    prompt: str,
    snippets: list[EvidenceSnippet],
    *,
    evidence_selection: str,
    evidence_top_k: int,
) -> list[EvidenceSnippet]:
    if evidence_selection not in VALID_EVIDENCE_SELECTIONS:
        raise ValueError(f"unknown evidence_selection: {evidence_selection}")
    if evidence_selection == "all":
        return snippets
    if evidence_selection == "first":
        return snippets[:1]
    ranked = sorted(
        snippets,
        key=lambda snippet: (_snippet_score(prompt, snippet), snippet.path, snippet.start_line),
        reverse=True,
    )
    return ranked[: max(1, evidence_top_k)]


def _build_retrieval_diagnostics(
    task: RealTask,
    snippets: list[EvidenceSnippet],
    *,
    evidence_source: str,
    retrieval_mode: str,
    retrieval_top_k: int,
    evidence_selection: str,
    evidence_top_k: int,
) -> dict[str, Any]:
    retrieved_paths = [snippet.path for snippet in snippets]
    gold_files = list(task.gold_files)
    retrieved_gold_files = [path for path in retrieved_paths if path in set(gold_files)]
    missed_gold_files = [path for path in gold_files if path not in set(retrieved_paths)]
    gold_file_recall = len(retrieved_gold_files) / len(gold_files) if gold_files else 0.0
    return {
        "evidence_source": evidence_source,
        "retrieval_mode": retrieval_mode if evidence_source == "retrieval" else "",
        "retrieval_top_k": retrieval_top_k if evidence_source == "retrieval" else 0,
        "evidence_selection": evidence_selection,
        "evidence_top_k": evidence_top_k,
        "retrieved_paths": retrieved_paths,
        "gold_files": gold_files,
        "retrieved_gold_files": retrieved_gold_files,
        "missed_gold_files": missed_gold_files,
        "retrieved_gold_count": len(retrieved_gold_files),
        "missed_gold_count": len(missed_gold_files),
        "gold_file_recall": gold_file_recall,
        "has_any_gold_hit": bool(retrieved_gold_files),
    }


def build_provider_request(
    manifest: BenchmarkManifest,
    task: RealTask,
    *,
    instruction_mode: InstructionMode = InstructionMode.NONE,
    evidence_source: str = "gold",
    retrieval_mode: str = "task_aware",
    retrieval_top_k: int = 2,
    evidence_selection: str = "all",
    evidence_top_k: int = 1,
) -> tuple[ProviderRequest, InstructionLoad, list[str]]:
    repo = manifest.repo(task.repo_id)
    repo_root = repo.root_path()
    area = _repo_area(task)
    instruction = load_instructions(instruction_mode, area)
    if evidence_source not in VALID_EVIDENCE_SOURCES:
        raise ValueError(f"unknown evidence_source: {evidence_source}")
    if retrieval_mode not in VALID_RETRIEVAL_MODES:
        raise ValueError(f"unknown retrieval_mode: {retrieval_mode}")

    snippets: list[EvidenceSnippet] = []
    missing_paths: list[str] = []
    if evidence_source == "gold":
        for span in task.gold_evidence_spans:
            candidate = repo_root / span.path
            if not candidate.exists():
                missing_paths.append(span.path)
                continue
            snippets.append(
                EvidenceSnippet(
                    path=span.path,
                    start_line=span.start_line,
                    end_line=span.end_line,
                    text=_read_lines(candidate, span.start_line, span.end_line),
                )
            )
    else:
        snippets = retrieve_repo_chunks(
            repo_root,
            task.prompt,
            mode=retrieval_mode,
            task_class=task.task_class,
            top_k=retrieval_top_k,
        )
    for rel_path in task.gold_files:
        candidate = repo_root / rel_path
        if not candidate.exists() and rel_path not in missing_paths:
            missing_paths.append(rel_path)

    selected_snippets = (
        _select_snippets(
            task.prompt,
            snippets,
            evidence_selection=evidence_selection,
            evidence_top_k=evidence_top_k,
        )
        if evidence_source == "gold"
        else snippets
    )

    request = ProviderRequest(
        task_id=task.task_id,
        repo_root=str(repo_root),
        prompt=task.prompt,
        expected_artifact_type=task.expected_artifact_type,
        allowed_tools=task.allowed_tools,
        instruction_mode=instruction.mode,
        instruction_tokens=instruction.token_cost,
        context_snippets=selected_snippets,
        gold_files=task.gold_files,
    )
    return request, instruction, sorted(set(missing_paths))


def run_real_task(
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
) -> RuntimeAttemptArtifact:
    task = next(task for task in manifest.tasks if task.task_id == task_id)
    request, instruction, missing_paths = build_provider_request(
        manifest,
        task,
        instruction_mode=instruction_mode,
        evidence_source=evidence_source,
        retrieval_mode=retrieval_mode,
        retrieval_top_k=retrieval_top_k,
        evidence_selection=evidence_selection,
        evidence_top_k=evidence_top_k,
    )
    response: ProviderResponse = provider.run(request)
    retrieval_diagnostics = _build_retrieval_diagnostics(
        task,
        request.context_snippets,
        evidence_source=evidence_source,
        retrieval_mode=retrieval_mode,
        retrieval_top_k=retrieval_top_k,
        evidence_selection=evidence_selection,
        evidence_top_k=evidence_top_k,
    )
    ready = not missing_paths
    return RuntimeAttemptArtifact(
        task_id=task.task_id,
        repo_id=task.repo_id,
        repo_root=request.repo_root,
        instruction=instruction.to_dict(),
        request=request.to_dict(),
        response=response.to_dict(),
        retrieval_diagnostics=retrieval_diagnostics,
        ready=ready,
        missing_paths=missing_paths,
    )
