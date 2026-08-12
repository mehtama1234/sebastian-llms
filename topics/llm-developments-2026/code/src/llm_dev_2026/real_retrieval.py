from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .provider import EvidenceSnippet
from .text import tokenize

TEXT_EXTENSIONS = {".py", ".md", ".toml", ".sh", ".txt", ".json", ".yaml", ".yml"}
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".coding-agent-v1",
    "evals",
    "notes",
    "artifacts",
}
_QUERY_EXPANSIONS = {
    "architecture": {"architecture", "arch", "design"},
    "advances": {"advances", "advance"},
    "compressed": {"compressed", "compression"},
    "attention": {"attention", "attn"},
    "context": {"context", "history"},
    "long": {"long", "extended"},
    "verifier": {"verifier", "verification", "verify", "check"},
    "meta": {"meta", "auditor", "audit"},
    "benchmark": {"benchmark", "bench", "evaluation"},
    "loader": {"loader", "load", "loading"},
    "tests": {"tests", "test", "pytest"},
    "production": {"production", "prod"},
    "experiment": {"experiment", "experiments"},
    "goal": {"goal", "plan", "checklist"},
}
_AREA_HINTS = {
    "architecture": "architecture-advances-2026",
    "advances": "architecture-advances-2026",
    "verifier": "llm-developments-2026",
    "meta": "llm-developments-2026",
    "benchmark": "llm-developments-2026",
    "loader": "llm-developments-2026",
    "production": "llm-developments-2026",
    "experiment": "llm-developments-2026",
}


@dataclass(slots=True)
class RepoChunk:
    path: str
    start_line: int
    end_line: int
    text: str
    score: float

    def to_snippet(self) -> EvidenceSnippet:
        return EvidenceSnippet(
            path=self.path,
            start_line=self.start_line,
            end_line=self.end_line,
            text=self.text,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "text": self.text,
            "score": self.score,
        }


def _path_tokens(path: str) -> list[str]:
    return tokenize(path.replace("/", " ").replace(".", " ").replace("_", " "))


def _bigrams(tokens: list[str]) -> set[str]:
    return {" ".join(tokens[idx : idx + 2]) for idx in range(len(tokens) - 1)}


def _expand_query_tokens(query_tokens: set[str]) -> set[str]:
    expanded = set(query_tokens)
    for token in list(query_tokens):
        expanded.update(_QUERY_EXPANSIONS.get(token, {token}))
    return expanded


def _area_targets(query_tokens: set[str]) -> set[str]:
    return {target for token in query_tokens for hint, target in _AREA_HINTS.items() if token == hint}


def _path_quality_penalty(path: str) -> float:
    normalized = f"/{path.lower()}"
    penalty = 0.0
    if normalized.endswith("/readme.md"):
        penalty += 1.2
    if ".egg-info/" in normalized:
        penalty += 4.0
    if "/artifacts/" in normalized:
        penalty += 5.0
    if normalized.endswith("/sources.txt"):
        penalty += 4.0
    return penalty


def _source_family(path: str) -> str:
    normalized = path.lower()
    if "/code/src/" in f"/{normalized}":
        return "code"
    if "/code/tests/" in f"/{normalized}" or "/tests/" in f"/{normalized}":
        return "tests"
    if "/docs/" in f"/{normalized}":
        return "docs"
    if "/projects/" in f"/{normalized}":
        return "projects"
    if normalized.endswith("readme.md"):
        return "readme"
    return "other"


def _task_family_slots(task_class: str | None) -> list[str]:
    if task_class == "inspect":
        return ["code", "code", "docs", "projects", "readme", "tests", "other"]
    if task_class == "diagnose":
        return ["code", "code", "tests", "docs", "projects", "readme", "other"]
    if task_class == "bug_fix":
        return ["code", "tests", "code", "docs", "projects", "readme", "other"]
    if task_class == "research":
        return ["projects", "docs", "code", "readme", "tests", "other"]
    return ["code", "docs", "projects", "tests", "readme", "other"]


def _task_mode_path_bonus(task_class: str | None, query_terms: list[str], path: str) -> float:
    normalized = path.lower()
    filename_tokens = set(tokenize(Path(path).name.replace(".", " ").replace("_", " ")))
    query_token_set = set(query_terms)
    bonus = 0.0

    if task_class == "inspect":
        if normalized.endswith("long_context_eval.py"):
            bonus += 8.0
        if "assessment" in filename_tokens:
            bonus += 4.0
        if "followup" in filename_tokens:
            bonus -= 3.0
        if any(token in query_token_set for token in {"tradeoffs", "tradeoff"}):
            if normalized.endswith("long_context_eval.py"):
                bonus += 2.0
            if "assessment" in filename_tokens:
                bonus += 1.5
        if any(token in filename_tokens for token in {"memo", "remediation", "plan"}):
            bonus -= 3.0
    elif task_class == "diagnose":
        if normalized.endswith("meta_verifier.py"):
            bonus += 4.0
        if normalized.endswith("verifier.py") or normalized.endswith("harness.py"):
            bonus += 2.5
        if normalized.endswith("test_real_retrieval.py"):
            bonus -= 2.0
    elif task_class == "bug_fix":
        if normalized.endswith("benchmark_loader.py"):
            bonus += 4.0
        if normalized.endswith("test_benchmark_schema.py"):
            bonus += 3.5
        if normalized.endswith("test_real_retrieval.py"):
            bonus -= 2.5
    elif task_class == "research":
        if "/projects/" in f"/{normalized}":
            bonus += 2.0
        if normalized.endswith("checklist.md"):
            bonus += 2.5

    return bonus


def _iter_task_entrypoint_snippets(
    repo_root: Path,
    *,
    task_class: str | None,
    query_tokens: set[str],
) -> list[EvidenceSnippet]:
    if task_class is None:
        return []
    area_targets = _area_targets(query_tokens) or {
        "architecture-advances-2026",
        "llm-developments-2026",
    }
    snippets: list[EvidenceSnippet] = []
    for target in sorted(area_targets):
        root = repo_root / target
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            rel_path = str(path.relative_to(repo_root))
            normalized = rel_path.lower()
            if task_class == "inspect":
                keep = normalized.endswith("long_context_eval.py") or normalized.endswith("assessment.py")
            elif task_class == "diagnose":
                keep = normalized.endswith("meta_verifier.py") or normalized.endswith("verifier.py") or normalized.endswith("harness.py")
            elif task_class == "bug_fix":
                keep = normalized.endswith("benchmark_loader.py") or normalized.endswith("benchmark_schema.py")
            elif task_class == "research":
                keep = normalized.endswith("retrieval.py") or normalized.endswith("experiment.py")
            else:
                keep = False
            if not keep:
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            if not lines:
                continue
            end_line = min(len(lines), 40)
            snippets.append(
                EvidenceSnippet(
                    path=rel_path,
                    start_line=1,
                    end_line=end_line,
                    text="\n".join(lines[:end_line]),
                )
            )
    return snippets


def _file_score(
    query_tokens: set[str],
    expanded_query_tokens: set[str],
    query_terms: list[str],
    path: str,
) -> float:
    path_tokens = _path_tokens(path)
    filename_tokens = tokenize(Path(path).name.replace(".", " ").replace("_", " "))
    query_bigrams = _bigrams(query_terms)
    path_bigrams = _bigrams(path_tokens)
    filename_bigrams = _bigrams(filename_tokens)
    raw_overlap = len(set(path_tokens) & query_tokens)
    expanded_overlap = len(set(path_tokens) & expanded_query_tokens)
    filename_overlap = len(set(filename_tokens) & expanded_query_tokens)
    path_phrase_overlap = len(path_bigrams & query_bigrams)
    filename_phrase_overlap = len(filename_bigrams & query_bigrams)
    area_bonus = 3.0 if any(path.startswith(target + "/") for target in _area_targets(query_tokens)) else 0.0
    code_bonus = 3.0 if "/code/src/" in f"/{path}" else 0.0
    test_bonus = 2.0 if "/tests/" in f"/{path}" and "test" in expanded_query_tokens else 0.0
    docs_bonus = 1.0 if "/docs/" in f"/{path}" else 0.0
    return (
        3.5 * raw_overlap
        + 1.2 * expanded_overlap
        + 5.0 * filename_overlap
        + 3.0 * path_phrase_overlap
        + 8.0 * filename_phrase_overlap
        + area_bonus
        + code_bonus
        + test_bonus
        + docs_bonus
        - _path_quality_penalty(path)
    )


def _chunk_score(
    query_tokens: set[str],
    expanded_query_tokens: set[str],
    query_terms: list[str],
    path: str,
    text: str,
) -> float:
    text_tokens = tokenize(text)
    path_tokens = _path_tokens(path)
    filename_tokens = tokenize(Path(path).name.replace(".", " ").replace("_", " "))
    query_bigrams = _bigrams(query_terms)
    path_bigrams = _bigrams(path_tokens)
    filename_bigrams = _bigrams(filename_tokens)
    path_overlap = sum(1 for token in path_tokens if token in query_tokens)
    expanded_path_overlap = sum(1 for token in path_tokens if token in expanded_query_tokens)
    filename_overlap = sum(1 for token in filename_tokens if token in expanded_query_tokens)
    text_overlap = sum(1 for token in text_tokens if token in query_tokens)
    expanded_text_overlap = sum(1 for token in text_tokens if token in expanded_query_tokens)
    unique_text_overlap = len(set(text_tokens) & query_tokens)
    unique_expanded_text_overlap = len(set(text_tokens) & expanded_query_tokens)
    path_phrase_overlap = len(path_bigrams & query_bigrams)
    filename_phrase_overlap = len(filename_bigrams & query_bigrams)
    code_bonus = 2.0 if "/code/src/" in f"/{path}" else 0.0
    test_bonus = 1.5 if "/tests/" in f"/{path}" and ("tests" in expanded_query_tokens or "test" in expanded_query_tokens) else 0.0
    docs_bonus = 0.8 if "/docs/" in f"/{path}" else 0.0
    notes_penalty = 1.5 if "/notes/" in f"/{path}" else 0.0
    return float(
        unique_text_overlap
        + 0.35 * text_overlap
        + 2.5 * path_overlap
        + 0.25 * expanded_text_overlap
        + 0.8 * unique_expanded_text_overlap
        + 0.6 * expanded_path_overlap
        + 4.0 * filename_overlap
        + 2.5 * path_phrase_overlap
        + 8.0 * filename_phrase_overlap
        + code_bonus
        + test_bonus
        + docs_bonus
        - notes_penalty
        - _path_quality_penalty(path)
    )


def _iter_candidate_files(repo_root: Path, *, max_files: int) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") or part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if any(part.endswith(".egg-info") for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > 250_000:
                continue
        except OSError:
            continue
        files.append(path)

    def priority(path: Path) -> tuple[int, str]:
        rel = str(path.relative_to(repo_root))
        if "/code/src/" in f"/{rel}":
            bucket = 0
        elif "/docs/" in f"/{rel}":
            bucket = 1
        else:
            bucket = 2
        return (bucket, rel)

    files.sort(key=priority)
    return files[:max_files]


def retrieve_repo_chunks(
    repo_root: str | Path,
    query: str,
    *,
    mode: str = "lexical",
    task_class: str | None = None,
    top_k: int = 2,
    chunk_lines: int = 40,
    stride_lines: int = 30,
    max_files: int = 1000,
    shortlist_size: int = 12,
) -> list[EvidenceSnippet]:
    repo_root = Path(repo_root)
    query_terms = tokenize(query)
    query_tokens = set(query_terms)
    expanded_query_tokens = _expand_query_tokens(query_tokens)
    if mode not in {"lexical", "sparse", "task_aware"}:
        raise ValueError(f"unknown retrieval mode: {mode}")
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    chunks: list[RepoChunk] = []
    candidate_files = _iter_candidate_files(repo_root, max_files=max_files)
    ranked_files = sorted(
        candidate_files,
        key=lambda path: (
            _file_score(
                query_tokens,
                expanded_query_tokens,
                query_terms,
                str(path.relative_to(repo_root)),
            ),
            str(path.relative_to(repo_root)),
        ),
        reverse=True,
    )
    for path in ranked_files[: max(shortlist_size * 4, top_k * 12)]:
        try:
            lines = path.read_text().splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        rel_path = str(path.relative_to(repo_root))
        if not lines:
            continue
        step = max(1, stride_lines)
        size = max(1, chunk_lines)
        for start in range(0, len(lines), step):
            end = min(len(lines), start + size)
            text = "\n".join(lines[start:end])
            score = _chunk_score(query_tokens, expanded_query_tokens, query_terms, rel_path, text)
            if score <= 0:
                continue
            chunks.append(
                RepoChunk(
                    path=rel_path,
                    start_line=start + 1,
                    end_line=end,
                    text=text,
                    score=score,
                )
            )
    if mode == "lexical":
        ranked = sorted(chunks, key=lambda chunk: (chunk.score, chunk.path, -chunk.start_line), reverse=True)
        return [chunk.to_snippet() for chunk in _unique_top_chunks(ranked, top_k)]

    shortlist = sorted(chunks, key=lambda chunk: (chunk.score, chunk.path, -chunk.start_line), reverse=True)[:shortlist_size]
    reranked = sorted(
        shortlist,
        key=lambda chunk: (
            _chunk_score(query_tokens, expanded_query_tokens, query_terms, chunk.path, chunk.text)
            + 0.2 * len(set(tokenize(chunk.text)) & query_tokens),
            chunk.path,
            -chunk.start_line,
        ),
        reverse=True,
    )
    if mode == "sparse":
        return [chunk.to_snippet() for chunk in _unique_top_chunks(reranked, top_k)]

    ranked_snippets = [chunk.to_snippet() for chunk in _unique_top_chunks(reranked, shortlist_size)]
    ranked_snippets.extend(
        _iter_task_entrypoint_snippets(
            repo_root,
            task_class=task_class,
            query_tokens=query_tokens,
        )
    )
    unique_ranked_snippets: list[EvidenceSnippet] = []
    seen_snippet_keys: set[str] = set()
    for snippet in ranked_snippets:
        key = f"{snippet.path}:{snippet.start_line}:{snippet.end_line}"
        if key in seen_snippet_keys:
            continue
        seen_snippet_keys.add(key)
        unique_ranked_snippets.append(snippet)
    selected: list[EvidenceSnippet] = []
    seen_keys: set[str] = set()
    slots = _task_family_slots(task_class)
    scored = sorted(
        unique_ranked_snippets,
        key=lambda snippet: (
            _chunk_score(query_tokens, expanded_query_tokens, query_terms, snippet.path, snippet.text)
            + _task_mode_path_bonus(task_class, query_terms, snippet.path),
            snippet.path,
            -snippet.start_line,
        ),
        reverse=True,
    )
    for family in slots:
        if len(selected) >= top_k:
            break
        for snippet in scored:
            key = f"{snippet.path}:{snippet.start_line}:{snippet.end_line}"
            if key in seen_keys or _source_family(snippet.path) != family:
                continue
            selected.append(snippet)
            seen_keys.add(key)
            break
    for snippet in scored:
        if len(selected) >= top_k:
            break
        key = f"{snippet.path}:{snippet.start_line}:{snippet.end_line}"
        if key in seen_keys:
            continue
        selected.append(snippet)
        seen_keys.add(key)
    return selected[:top_k]


def _unique_top_chunks(chunks: list[RepoChunk], top_k: int) -> list[RepoChunk]:
    selected: list[RepoChunk] = []
    seen_paths: set[str] = set()
    for chunk in chunks:
        if chunk.path in seen_paths:
            continue
        selected.append(chunk)
        seen_paths.add(chunk.path)
        if len(selected) >= top_k:
            break
    return selected
