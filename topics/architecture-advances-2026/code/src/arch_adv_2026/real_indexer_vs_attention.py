from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .indexer_vs_attention import _expand_terms, _rare_terms, _tokenize


def _ensure_llm_dev_imports() -> None:
    try:
        import llm_dev_2026  # noqa: F401
    except ModuleNotFoundError:
        sibling_src = (
            Path(__file__).resolve().parents[4] / "llm-developments-2026" / "code" / "src"
        )
        if str(sibling_src) not in sys.path:
            sys.path.insert(0, str(sibling_src))


_ensure_llm_dev_imports()

from llm_dev_2026.benchmark_loader import load_benchmark_manifest
from llm_dev_2026.provider import EvidenceSnippet
from llm_dev_2026.real_retrieval import retrieve_repo_chunks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare budgeted chunk-selection strategies on real benchmark tasks."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--budgets", nargs="+", type=int, default=[1, 2, 3])
    parser.add_argument("--candidate-pool-k", type=int, default=6)
    parser.add_argument("--stdout", action="store_true")
    return parser


def _dedupe_snippets(snippets: list[EvidenceSnippet]) -> list[EvidenceSnippet]:
    deduped: list[EvidenceSnippet] = []
    seen: set[str] = set()
    for snippet in snippets:
        key = f"{snippet.path}:{snippet.start_line}:{snippet.end_line}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(snippet)
    return deduped


def _support_paths(task: Any) -> list[str]:
    span_paths = [span.path for span in task.gold_evidence_spans]
    if span_paths:
        return sorted(set(span_paths))
    return sorted(set(task.gold_files))


def _task_area_prefixes(task: Any) -> list[str]:
    prefixes: set[str] = set()
    for path in [*task.gold_files, *[span.path for span in task.gold_evidence_spans]]:
        parts = Path(path).parts
        if parts:
            prefixes.add(parts[0])
    return sorted(prefixes)


def _is_noise_path(path: str) -> bool:
    normalized = f"/{path.lower()}"
    return any(
        marker in normalized
        for marker in [
            "/artifacts/",
            ".egg-info/",
            "/node_modules/",
            "/__pycache__/",
            "/.venv/",
        ]
    ) or normalized.endswith("/sources.txt")


def _filename_tokens(path: str) -> list[str]:
    return _tokenize(Path(path).name)


def _real_lexical_score(prompt: str, snippet: EvidenceSnippet, *, area_prefixes: list[str]) -> float:
    prompt_terms = set(_tokenize(prompt))
    path_terms = set(_tokenize(snippet.path.replace("/", " ")))
    file_terms = set(_filename_tokens(snippet.path))
    text_terms = _tokenize(snippet.text)
    path_overlap = len(prompt_terms & path_terms)
    file_overlap = len(prompt_terms & file_terms)
    text_overlap = sum(1 for token in text_terms if token in prompt_terms)
    unique_text_overlap = len(set(text_terms) & prompt_terms)
    code_bonus = 1.2 if "/code/src/" in f"/{snippet.path}" else 0.0
    docs_bonus = 0.4 if "/docs/" in f"/{snippet.path}" else 0.0
    area_bonus = 2.4 if any(snippet.path.startswith(prefix + "/") for prefix in area_prefixes) else 0.0
    artifact_penalty = 4.0 if _is_noise_path(snippet.path) else 0.0
    return (
        2.4 * path_overlap
        + 3.0 * file_overlap
        + 0.35 * text_overlap
        + 1.0 * unique_text_overlap
        + code_bonus
        + docs_bonus
        + area_bonus
        - artifact_penalty
    )


def _real_structured_breakdown(
    prompt: str,
    snippet: EvidenceSnippet,
    *,
    area_prefixes: list[str],
) -> dict[str, float]:
    raw_prompt_terms = set(_tokenize(prompt))
    raw_text_terms = set(_tokenize(snippet.text))
    raw_path_terms = set(_tokenize(snippet.path.replace("/", " ")))
    prompt_terms = set(_expand_terms(_tokenize(prompt)))
    text_terms = set(_expand_terms(_tokenize(snippet.text)))
    path_terms = set(_expand_terms(_tokenize(snippet.path.replace("/", " "))))
    rare_terms = _rare_terms(prompt)

    raw_path_overlap = len(raw_prompt_terms & raw_path_terms)
    raw_text_overlap = len(raw_prompt_terms & raw_text_terms)
    synonym_path_overlap = len((prompt_terms & path_terms) - (raw_prompt_terms & raw_path_terms))
    synonym_text_overlap = len((prompt_terms & text_terms) - (raw_prompt_terms & raw_text_terms))
    rare_overlap = len(rare_terms & (text_terms | path_terms))
    rare_ratio = rare_overlap / len(rare_terms) if rare_terms else 0.0
    filename_overlap = len(set(_filename_tokens(snippet.path)) & raw_prompt_terms)
    code_bonus = 1.4 if "/code/src/" in f"/{snippet.path}" else 0.0
    readme_penalty = -0.6 if Path(snippet.path).name.lower() == "readme.md" and raw_path_overlap == 0 else 0.0
    area_bonus = 2.8 if any(snippet.path.startswith(prefix + "/") for prefix in area_prefixes) else 0.0
    artifact_penalty = -5.0 if _is_noise_path(snippet.path) else 0.0

    return {
        "path_overlap": 2.6 * raw_path_overlap,
        "filename_overlap": 3.4 * filename_overlap,
        "text_overlap": 1.1 * raw_text_overlap,
        "synonym_path_overlap": 0.8 * synonym_path_overlap,
        "synonym_text_overlap": 0.45 * synonym_text_overlap,
        "rare_term_coverage": 2.8 * rare_ratio,
        "code_bonus": code_bonus,
        "readme_penalty": readme_penalty,
        "area_bonus": area_bonus,
        "artifact_penalty": artifact_penalty,
    }


def _real_structured_score(prompt: str, snippet: EvidenceSnippet, *, area_prefixes: list[str]) -> float:
    return sum(_real_structured_breakdown(prompt, snippet, area_prefixes=area_prefixes).values())


def _anchor_score(snippet: EvidenceSnippet) -> tuple[float, str]:
    path = snippet.path.lower()
    score = 0.0
    if path.endswith("readme.md"):
        score += 2.0
    if "/docs/" in f"/{path}":
        score += 1.4
    if "/code/src/" in f"/{path}":
        score += 0.8
    return score, path


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


def _task_family_slots(task_class: str) -> list[str]:
    if task_class == "inspect":
        return ["code", "code", "docs", "projects", "readme", "tests", "other"]
    if task_class == "diagnose":
        return ["code", "code", "tests", "docs", "projects", "readme", "other"]
    if task_class == "bug_fix":
        return ["code", "tests", "code", "docs", "projects", "readme", "other"]
    if task_class == "research":
        return ["projects", "docs", "code", "readme", "tests", "other"]
    return ["code", "docs", "projects", "tests", "readme", "other"]


def _task_specific_path_bonus(task_class: str, prompt: str, snippet: EvidenceSnippet) -> float:
    path = snippet.path.lower()
    filename_tokens = set(_filename_tokens(path))
    prompt_terms = set(_tokenize(prompt))
    bonus = 0.0

    if task_class == "inspect":
        if "/code/src/" in f"/{path}" and (
            "assessment" in filename_tokens
            or "eval" in filename_tokens
            or "evaluation" in filename_tokens
        ):
            bonus += 4.0
        if path.endswith("long_context_eval.py"):
            bonus += 5.0
        if "tradeoffs" in prompt_terms or "tradeoff" in prompt_terms:
            if path.endswith("long_context_eval.py"):
                bonus += 2.0
            if "assessment" in filename_tokens:
                bonus += 1.5
        if any(token in filename_tokens for token in {"memo", "remediation", "plan"}):
            bonus -= 3.0

    if task_class == "diagnose":
        if path.endswith("meta_verifier.py"):
            bonus += 4.0
        if path.endswith("verifier.py") or path.endswith("harness.py"):
            bonus += 2.5
        if path.endswith("test_real_retrieval.py"):
            bonus -= 2.0

    if task_class == "bug_fix":
        if path.endswith("benchmark_loader.py"):
            bonus += 4.0
        if path.endswith("test_benchmark_schema.py"):
            bonus += 3.5
        if path.endswith("test_real_retrieval.py"):
            bonus -= 2.5

    if task_class == "research":
        if "/projects/" in f"/{path}":
            bonus += 2.0
        if path.endswith("checklist.md"):
            bonus += 2.5

    return bonus


def _iter_entrypoint_candidates(repo_root: Path, area_prefixes: list[str], task_class: str) -> list[EvidenceSnippet]:
    candidates: list[EvidenceSnippet] = []
    for prefix in area_prefixes:
        root = repo_root / prefix
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            rel_path = str(path.relative_to(repo_root))
            normalized = rel_path.lower()
            if task_class == "inspect":
                keep = normalized.endswith("eval.py") or normalized.endswith("assessment.py")
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
            candidates.append(
                EvidenceSnippet(
                    path=rel_path,
                    start_line=1,
                    end_line=end_line,
                    text="\n".join(lines[:end_line]),
                )
            )
    return candidates


def _augment_union_pool(
    *,
    repo_root: Path,
    prompt: str,
    task_class: str,
    area_prefixes: list[str],
    union_pool: list[EvidenceSnippet],
) -> list[EvidenceSnippet]:
    entrypoints = _iter_entrypoint_candidates(repo_root, area_prefixes, task_class)
    if not entrypoints:
        return union_pool
    ranked = sorted(
        entrypoints,
        key=lambda snippet: (
            _real_structured_score(prompt, snippet, area_prefixes=area_prefixes)
            + _task_specific_path_bonus(task_class, prompt, snippet),
            snippet.path,
            -snippet.start_line,
        ),
        reverse=True,
    )
    return _dedupe_snippets([*union_pool, *ranked[:4]])


def _balanced_structured_selection(
    *,
    prompt: str,
    task_class: str,
    area_prefixes: list[str],
    union_pool: list[EvidenceSnippet],
    budget_k: int,
) -> list[EvidenceSnippet]:
    ranked = sorted(
        union_pool,
        key=lambda snippet: (
            _real_structured_score(prompt, snippet, area_prefixes=area_prefixes)
            + _task_specific_path_bonus(task_class, prompt, snippet),
            snippet.path,
            -snippet.start_line,
        ),
        reverse=True,
    )
    family_slots = _task_family_slots(task_class)
    selected: list[EvidenceSnippet] = []
    seen_keys: set[str] = set()

    for family in family_slots:
        if len(selected) >= budget_k:
            break
        for snippet in ranked:
            key = f"{snippet.path}:{snippet.start_line}:{snippet.end_line}"
            snippet_family = _source_family(snippet.path)
            if key in seen_keys or snippet_family != family:
                continue
            selected.append(snippet)
            seen_keys.add(key)
            break

    for snippet in ranked:
        if len(selected) >= budget_k:
            break
        key = f"{snippet.path}:{snippet.start_line}:{snippet.end_line}"
        if key in seen_keys:
            continue
        selected.append(snippet)
        seen_keys.add(key)

    return selected


def _select_variant(
    *,
    prompt: str,
    task_class: str,
    area_prefixes: list[str],
    lexical_pool: list[EvidenceSnippet],
    sparse_pool: list[EvidenceSnippet],
    union_pool: list[EvidenceSnippet],
    variant: str,
    budget_k: int,
) -> list[EvidenceSnippet]:
    if variant == "lexical_retrieval_order":
        return lexical_pool[:budget_k]
    if variant == "sparse_retrieval_order":
        return sparse_pool[:budget_k]
    if variant == "anchor_then_tail":
        anchors = sorted(union_pool, key=_anchor_score, reverse=True)
        return anchors[:budget_k]
    if variant == "union_lexical_rerank":
        ranked = sorted(
            union_pool,
            key=lambda snippet: (
                _real_lexical_score(prompt, snippet, area_prefixes=area_prefixes),
                snippet.path,
                -snippet.start_line,
            ),
            reverse=True,
        )
        return ranked[:budget_k]
    if variant == "union_structured_rerank":
        ranked = sorted(
            union_pool,
            key=lambda snippet: (
                _real_structured_score(prompt, snippet, area_prefixes=area_prefixes),
                snippet.path,
                -snippet.start_line,
            ),
            reverse=True,
        )
        return ranked[:budget_k]
    if variant == "task_aware_balanced_rerank":
        return _balanced_structured_selection(
            prompt=prompt,
            task_class=task_class,
            area_prefixes=area_prefixes,
            union_pool=union_pool,
            budget_k=budget_k,
        )
    raise ValueError(f"unknown variant: {variant}")


def _snippet_token_cost(snippets: list[EvidenceSnippet]) -> int:
    return sum(len(snippet.text.split()) for snippet in snippets)


def _variant_diagnostics(
    prompt: str,
    snippets: list[EvidenceSnippet],
    *,
    variant: str,
    area_prefixes: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for snippet in snippets:
        if variant == "union_structured_rerank":
            breakdown = _real_structured_breakdown(prompt, snippet, area_prefixes=area_prefixes)
            score = sum(breakdown.values())
        elif variant == "union_lexical_rerank":
            score = _real_lexical_score(prompt, snippet, area_prefixes=area_prefixes)
            breakdown = {"score": score}
        else:
            score = 0.0
            breakdown = {}
        rows.append(
            {
                "path": snippet.path,
                "start_line": snippet.start_line,
                "end_line": snippet.end_line,
                "score": score,
                "breakdown": breakdown,
            }
        )
    return sorted(rows, key=lambda row: (row["score"], row["path"], -row["start_line"]), reverse=True)


def build_real_indexer_vs_attention_report(
    manifest_path: str | Path,
    *,
    budgets: list[int] | None = None,
    candidate_pool_k: int = 6,
) -> dict[str, Any]:
    manifest = load_benchmark_manifest(manifest_path)
    budgets = budgets or [1, 2, 3]
    variants = [
        "lexical_retrieval_order",
        "sparse_retrieval_order",
        "anchor_then_tail",
        "union_lexical_rerank",
        "union_structured_rerank",
        "task_aware_balanced_rerank",
    ]

    rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for task in manifest.tasks:
        repo_root = manifest.repo(task.repo_id).root_path()
        lexical_pool = _dedupe_snippets(
            retrieve_repo_chunks(repo_root, task.prompt, mode="lexical", top_k=candidate_pool_k)
        )
        sparse_pool = _dedupe_snippets(
            retrieve_repo_chunks(repo_root, task.prompt, mode="sparse", top_k=candidate_pool_k)
        )
        lexical_pool = [snippet for snippet in lexical_pool if not _is_noise_path(snippet.path)]
        sparse_pool = [snippet for snippet in sparse_pool if not _is_noise_path(snippet.path)]
        union_pool = _dedupe_snippets([*lexical_pool, *sparse_pool])
        support_paths = _support_paths(task)
        area_prefixes = _task_area_prefixes(task)
        union_pool = _augment_union_pool(
            repo_root=repo_root,
            prompt=task.prompt,
            task_class=task.task_class,
            area_prefixes=area_prefixes,
            union_pool=union_pool,
        )

        diagnostics.append(
            {
                "task_id": task.task_id,
                "support_paths": support_paths,
                "union_structured_rerank": _variant_diagnostics(
                    task.prompt,
                    union_pool,
                    variant="union_structured_rerank",
                    area_prefixes=area_prefixes,
                )[:5],
                "union_lexical_rerank": _variant_diagnostics(
                    task.prompt,
                    union_pool,
                    variant="union_lexical_rerank",
                    area_prefixes=area_prefixes,
                )[:5],
            }
        )

        for variant in variants:
            for budget_k in budgets:
                selected = _select_variant(
                    prompt=task.prompt,
                    task_class=task.task_class,
                    area_prefixes=area_prefixes,
                    lexical_pool=lexical_pool,
                    sparse_pool=sparse_pool,
                    union_pool=union_pool,
                    variant=variant,
                    budget_k=budget_k,
                )
                selected_paths = [snippet.path for snippet in selected]
                support_hits = len({path for path in selected_paths if path in set(support_paths)})
                support_recall = support_hits / len(support_paths) if support_paths else 1.0
                exact_support_hit = support_hits == len(support_paths) if support_paths else True
                rows.append(
                    {
                        "task_id": task.task_id,
                        "task_class": task.task_class,
                        "difficulty": task.difficulty,
                        "long_context": task.long_context,
                        "variant": variant,
                        "budget_k": budget_k,
                        "candidate_pool_size": len(union_pool),
                        "selected_paths": selected_paths,
                        "support_paths": support_paths,
                        "support_recall": support_recall,
                        "exact_support_hit": exact_support_hit,
                        "any_support_hit": support_hits > 0,
                        "prompt_token_cost": _snippet_token_cost(selected),
                    }
                )

    summary: dict[str, dict[str, Any]] = {}
    for variant in variants:
        variant_rows = [row for row in rows if row["variant"] == variant]
        summary[variant] = {
            "mean_support_recall": sum(row["support_recall"] for row in variant_rows) / len(variant_rows),
            "mean_any_support_hit_rate": (
                sum(1.0 if row["any_support_hit"] else 0.0 for row in variant_rows) / len(variant_rows)
            ),
            "mean_exact_support_hit_rate": (
                sum(1.0 if row["exact_support_hit"] else 0.0 for row in variant_rows) / len(variant_rows)
            ),
            "mean_prompt_token_cost": sum(row["prompt_token_cost"] for row in variant_rows) / len(variant_rows),
            "budgets": budgets,
        }

    return {
        "manifest_path": str(manifest_path),
        "benchmark_id": manifest.benchmark_id,
        "task_count": len(manifest.tasks),
        "variants": variants,
        "budgets": budgets,
        "candidate_pool_k": candidate_pool_k,
        "rows": rows,
        "summary": summary,
        "diagnostics": diagnostics,
        "notes": [
            "This bridge uses the real benchmark manifest and real repo-chunk retrieval, but scoring remains retrieval-only.",
            "Support recall is measured against benchmark gold evidence paths or gold files, not final answer quality.",
            "Use this artifact to compare budgeted chunk selectors before adding heavier live-model execution."
        ],
    }


def render_real_indexer_vs_attention_markdown(report: dict[str, Any]) -> str:
    lines = ["# Real Indexer vs Attention Report", ""]
    lines.append("## Summary")
    lines.append("")
    lines.append("| Variant | Mean Support Recall | Any Hit Rate | Exact Hit Rate | Mean Prompt Tokens | Budgets |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for variant, stats in report["summary"].items():
        lines.append(
            f"| `{variant}` | {stats['mean_support_recall']:.3f} | {stats['mean_any_support_hit_rate']:.3f} | "
            f"{stats['mean_exact_support_hit_rate']:.3f} | {stats['mean_prompt_token_cost']:.1f} | "
            f"{', '.join(str(b) for b in stats['budgets'])} |"
        )
    lines.append("")
    lines.append("## Rows")
    lines.append("")
    lines.append("| Task | Variant | Budget | Recall | Any Hit | Exact Hit | Prompt Tokens |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for row in report["rows"]:
        lines.append(
            f"| `{row['task_id']}` | `{row['variant']}` | {row['budget_k']} | {row['support_recall']:.3f} | "
            f"{str(row['any_support_hit']).lower()} | {str(row['exact_support_hit']).lower()} | {row['prompt_token_cost']} |"
        )
    lines.append("")
    lines.append("## Structured Diagnostics")
    lines.append("")
    for diagnostic in report["diagnostics"]:
        lines.append(f"### `{diagnostic['task_id']}`")
        lines.append("")
        lines.append("| Variant | Path | Score | Why It Ranked |")
        lines.append("|---|---|---:|---|")
        for key in ["union_structured_rerank", "union_lexical_rerank"]:
            label = key
            for row in diagnostic[key]:
                reason = ", ".join(
                    f"{name}={value:.2f}" for name, value in row["breakdown"].items() if value != 0.0
                ) or "score-only"
                lines.append(
                    f"| `{label}` | `{row['path']}:{row['start_line']}-{row['end_line']}` | {row['score']:.2f} | {reason} |"
                )
        lines.append("")
    return "\n".join(lines) + "\n"


def write_json_artifact(data: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return output_path


def write_markdown_artifact(markdown: str, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_real_indexer_vs_attention_report(
        args.manifest,
        budgets=args.budgets,
        candidate_pool_k=args.candidate_pool_k,
    )
    markdown = render_real_indexer_vs_attention_markdown(report)
    if args.artifact_json:
        path = write_json_artifact(report, args.artifact_json)
        print(f"Wrote real indexer-vs-attention JSON artifact to {path}")
    if args.artifact_md:
        path = write_markdown_artifact(markdown, args.artifact_md)
        print(f"Wrote real indexer-vs-attention markdown artifact to {path}")
    if args.stdout or not args.artifact_md:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
