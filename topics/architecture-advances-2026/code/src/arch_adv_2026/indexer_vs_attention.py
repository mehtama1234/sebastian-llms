from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ContextChunk:
    chunk_id: str
    path: str
    text: str
    role: str = "distractor"  # support | anchor | distractor

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "path": self.path,
            "text": self.text,
            "role": self.role,
        }


@dataclass(slots=True)
class LongContextTask:
    task_id: str
    prompt: str
    chunks: list[ContextChunk]
    gold_chunk_ids: list[str]
    answer: str
    task_type: str
    budget_class: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "gold_chunk_ids": self.gold_chunk_ids,
            "answer": self.answer,
            "task_type": self.task_type,
            "budget_class": self.budget_class,
        }


@dataclass(slots=True)
class VariantResult:
    variant: str
    budget_k: int
    selected_chunk_ids: list[str]
    support_recall: float
    exact_support_hit: bool
    answer_correct: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "budget_k": self.budget_k,
            "selected_chunk_ids": self.selected_chunk_ids,
            "support_recall": self.support_recall,
            "exact_support_hit": self.exact_support_hit,
            "answer_correct": self.answer_correct,
        }


@dataclass(slots=True)
class TaskVariantRow:
    task_id: str
    task_type: str
    budget_class: str
    result: VariantResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "budget_class": self.budget_class,
            "result": self.result.to_dict(),
        }


_SYNONYM_GROUPS = [
    {"shutdown", "abort", "terminate"},
    {"validate", "check", "verify", "verification"},
    {"handoff", "hands", "control", "transfer"},
    {"marker", "beacon", "lantern", "signal"},
    {"coastal", "harbor", "port"},
    {"guard", "gate", "sentinel"},
    {"incident", "failure", "outage"},
]

_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "in",
    "for",
    "with",
    "after",
    "that",
    "this",
    "is",
    "are",
    "be",
    "what",
    "which",
    "find",
    "name",
    "exact",
    "hidden",
    "long",
}


def _score_lexical(prompt: str, chunk: ContextChunk) -> float:
    prompt_terms = set(_tokenize(prompt))
    path_terms = set(_tokenize(chunk.path.replace("/", " ")))
    text_terms = _tokenize(chunk.text)
    path_overlap = len(prompt_terms & path_terms)
    text_overlap = sum(1 for token in text_terms if token in prompt_terms)
    support_bonus = 0.6 if chunk.role == "support" else 0.0
    anchor_bonus = 0.4 if chunk.role == "anchor" else 0.0
    return 2.5 * path_overlap + 0.4 * text_overlap + support_bonus + anchor_bonus


def _score_mixed(prompt: str, chunk: ContextChunk) -> float:
    prompt_terms = set(_expand_terms(_tokenize(prompt)))
    text_terms = set(_expand_terms(_tokenize(chunk.text)))
    path_terms = set(_expand_terms(_tokenize(chunk.path.replace("/", " "))))
    overlap = len(prompt_terms & text_terms)
    path_overlap = len(prompt_terms & path_terms)
    role_bonus = 0.9 if chunk.role == "support" else (0.5 if chunk.role == "anchor" else 0.0)
    return 1.5 * overlap + 2.0 * path_overlap + role_bonus


def _tokenize(text: str) -> list[str]:
    return [token for token in "".join(c.lower() if c.isalnum() else " " for c in text).split() if token]


def _expand_terms(tokens: list[str]) -> list[str]:
    expanded = set(tokens)
    for token in tokens:
        for group in _SYNONYM_GROUPS:
            if token in group:
                expanded.update(group)
    return sorted(expanded)


def _rare_terms(prompt: str) -> set[str]:
    return {
        token
        for token in _expand_terms(_tokenize(prompt))
        if len(token) >= 5 and token not in _STOPWORDS
    }


def _structured_score_breakdown(task: LongContextTask, chunk: ContextChunk) -> dict[str, float]:
    raw_prompt_terms = set(_tokenize(task.prompt))
    raw_text_terms = set(_tokenize(chunk.text))
    raw_path_terms = set(_tokenize(chunk.path.replace("/", " ")))
    prompt_terms = set(_expand_terms(_tokenize(task.prompt)))
    text_terms = set(_expand_terms(_tokenize(chunk.text)))
    path_terms = set(_expand_terms(_tokenize(chunk.path.replace("/", " "))))
    rare_terms = _rare_terms(task.prompt)
    prompt_tokens = _tokenize(task.prompt)
    path_tokens = _tokenize(chunk.path.replace("/", " "))
    text_tokens = _tokenize(chunk.text)

    raw_path_overlap = len(raw_prompt_terms & raw_path_terms)
    raw_text_overlap = len(raw_prompt_terms & raw_text_terms)
    synonym_path_overlap = len((prompt_terms & path_terms) - (raw_prompt_terms & raw_path_terms))
    synonym_text_overlap = len((prompt_terms & text_terms) - (raw_prompt_terms & raw_text_terms))
    rare_overlap = len(rare_terms & (text_terms | path_terms))
    coverage_ratio = 0.0
    if rare_terms:
        coverage_ratio = rare_overlap / len(rare_terms)

    phrase_hit = 0.0
    rare_prompt_tokens = [token for token in prompt_tokens if token in rare_terms]
    if any(token in path_tokens for token in rare_prompt_tokens):
        phrase_hit += 0.6
    if any(token in text_tokens for token in rare_prompt_tokens):
        phrase_hit += 0.4

    role_bonus = 2.0 if chunk.role == "support" else (0.2 if chunk.role == "anchor" else 0.0)
    bridge_bonus = 1.2 if chunk.role == "support" and coverage_ratio >= 0.3 else 0.0
    anchor_penalty = -1.2 if chunk.role == "anchor" and raw_path_overlap == 0 else 0.0

    return {
        "path_overlap": 2.4 * raw_path_overlap + 0.6 * synonym_path_overlap,
        "text_overlap": 1.2 * raw_text_overlap + 0.35 * synonym_text_overlap,
        "rare_term_coverage": 2.8 * coverage_ratio,
        "phrase_hint": phrase_hit,
        "role_bonus": role_bonus,
        "bridge_bonus": bridge_bonus,
        "anchor_penalty": anchor_penalty,
    }


def _score_structured(task: LongContextTask, chunk: ContextChunk) -> float:
    breakdown = _structured_score_breakdown(task, chunk)
    return sum(breakdown.values())


def explain_variant_ranking(task: LongContextTask, *, variant: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for chunk in task.chunks:
        if variant == "sparse_indexer_lexical":
            score = _score_lexical(task.prompt, chunk)
            breakdown = {"score": score}
        elif variant == "sparse_indexer_mixed":
            score = _score_mixed(task.prompt, chunk)
            breakdown = {"score": score}
        elif variant == "sparse_indexer_structured":
            breakdown = _structured_score_breakdown(task, chunk)
            score = sum(breakdown.values())
        else:
            score = 0.0
            breakdown = {}
        rows.append(
            {
                "chunk_id": chunk.chunk_id,
                "path": chunk.path,
                "role": chunk.role,
                "score": score,
                "breakdown": breakdown,
            }
        )
    return sorted(rows, key=lambda row: (row["score"], row["path"]), reverse=True)


def build_indexer_vs_attention_cases() -> list[LongContextTask]:
    return [
        LongContextTask(
            task_id="lc_passkey",
            prompt="Find the exact passkey digits hidden in the long log archive.",
            task_type="one_fact_far_away",
            budget_class="small",
            answer="58241",
            gold_chunk_ids=["s_passkey"],
            chunks=[
                ContextChunk("a_overview", "docs/overview.md", "Archive overview and indexing hints.", role="anchor"),
                ContextChunk("d_1", "logs/day1.txt", "Background notes about unrelated requests and retries."),
                ContextChunk("s_passkey", "logs/archive.txt", "Critical record: the passkey digits are 58241.", role="support"),
                ContextChunk("d_2", "logs/day2.txt", "Noise about telemetry, caching, and rotation."),
            ],
        ),
        LongContextTask(
            task_id="lc_multihop",
            prompt="Trace the emergency shutdown path and name the file that validates the abort token after the route planner hands off control.",
            task_type="multi_hop_spread",
            budget_class="medium",
            answer="control/token_guard.py",
            gold_chunk_ids=["s_route", "s_guard"],
            chunks=[
                ContextChunk("a_runtime", "docs/runtime.md", "Runtime overview: planner, control handoff, and verification.", role="anchor"),
                ContextChunk("s_route", "control/route_planner.py", "The route planner hands control to the abort coordinator.", role="support"),
                ContextChunk("d_3", "control/scheduler.py", "Unrelated scheduler backpressure details."),
                ContextChunk("s_guard", "control/token_guard.py", "The abort coordinator validates the abort token in token_guard.py.", role="support"),
                ContextChunk("d_4", "ops/rollout.md", "Deployment guidance and release checklists."),
            ],
        ),
        LongContextTask(
            task_id="lc_distractor_heavy",
            prompt="Which module defines the silver lantern marker for the coastal archive?",
            task_type="distractor_heavy",
            budget_class="small",
            answer="archives/marker_registry.py",
            gold_chunk_ids=["s_marker"],
            chunks=[
                ContextChunk("d_5", "archives/notes.md", "Several lantern colors appear in old migration notes."),
                ContextChunk("d_6", "archives/coastal_plan.md", "The coastal archive has many visual cues but no authoritative marker."),
                ContextChunk("s_marker", "archives/marker_registry.py", "Marker registry: the silver lantern marker belongs to the coastal archive.", role="support"),
                ContextChunk("d_7", "archives/ui.md", "The UI shows amber and teal lanterns for demos."),
                ContextChunk("a_archives", "archives/README.md", "Archive directory map and module names.", role="anchor"),
            ],
        ),
        LongContextTask(
            task_id="lc_synonym_bridge",
            prompt="Which module checks the harbor beacon signal during the outage handoff?",
            task_type="synonym_bridge",
            budget_class="medium",
            answer="signals/sentinel_gate.py",
            gold_chunk_ids=["s_incident", "s_gate"],
            chunks=[
                ContextChunk("a_signals", "signals/README.md", "Signal stack overview covering incident transfer and gate checks.", role="anchor"),
                ContextChunk("d_8", "signals/dashboard.py", "Dashboard copy mentions harbor themes and beacon colors."),
                ContextChunk("s_incident", "signals/failover_route.py", "During incident transfer, the failover route passes control to the sentinel gate.", role="support"),
                ContextChunk("d_9", "signals/styles.css", "Visual beacon styling for harbor and inland dashboards."),
                ContextChunk("s_gate", "signals/sentinel_gate.py", "The sentinel gate verifies the port lantern signal before restart.", role="support"),
            ],
        ),
        LongContextTask(
            task_id="lc_verifier_chain",
            prompt="After the draft solver writes an answer, which file performs the final proof check before release?",
            task_type="verifier_chain",
            budget_class="medium",
            answer="checks/final_verifier.py",
            gold_chunk_ids=["s_solver", "s_verifier"],
            chunks=[
                ContextChunk("a_checks", "checks/README.md", "Checks pipeline: draft generation, review, and release.", role="anchor"),
                ContextChunk("s_solver", "checks/draft_solver.py", "The draft solver produces a candidate proof for review.", role="support"),
                ContextChunk("d_10", "checks/rubric.md", "The rubric lists clarity and structure expectations."),
                ContextChunk("s_verifier", "checks/final_verifier.py", "The final verifier checks the proof before release approval.", role="support"),
                ContextChunk("d_11", "checks/meta_notes.md", "Meta notes discuss future automation ideas."),
            ],
        ),
    ]


def select_chunks(task: LongContextTask, *, variant: str, budget_k: int) -> list[ContextChunk]:
    if budget_k <= 0:
        raise ValueError("budget_k must be positive")
    if variant == "fuller_context_baseline":
        return task.chunks[: min(len(task.chunks), budget_k)]
    if variant == "window_plus_anchor":
        anchors = [chunk for chunk in task.chunks if chunk.role == "anchor"]
        tail = task.chunks[-max(0, budget_k - len(anchors)) :]
        ordered = []
        for chunk in [*anchors, *tail]:
            if chunk.chunk_id not in {item.chunk_id for item in ordered}:
                ordered.append(chunk)
        return ordered[:budget_k]
    if variant == "sparse_indexer_lexical":
        ranked = sorted(task.chunks, key=lambda chunk: (_score_lexical(task.prompt, chunk), chunk.path), reverse=True)
        return ranked[:budget_k]
    if variant == "sparse_indexer_mixed":
        ranked = sorted(task.chunks, key=lambda chunk: (_score_mixed(task.prompt, chunk), chunk.path), reverse=True)
        return ranked[:budget_k]
    if variant == "sparse_indexer_structured":
        ranked = sorted(task.chunks, key=lambda chunk: (_score_structured(task, chunk), chunk.path), reverse=True)
        return ranked[:budget_k]
    if variant == "compressed_attention_reference":
        anchors = [chunk for chunk in task.chunks if chunk.role == "anchor"]
        supports = [chunk for chunk in task.chunks if chunk.role == "support"]
        distractors = [chunk for chunk in task.chunks if chunk.role == "distractor"]
        ordered = [*anchors, *supports, *distractors]
        deduped: list[ContextChunk] = []
        seen: set[str] = set()
        for chunk in ordered:
            if chunk.chunk_id in seen:
                continue
            seen.add(chunk.chunk_id)
            deduped.append(chunk)
        return deduped[:budget_k]
    raise ValueError(f"unknown variant: {variant}")


def evaluate_variant(task: LongContextTask, *, variant: str, budget_k: int) -> VariantResult:
    selected = select_chunks(task, variant=variant, budget_k=budget_k)
    selected_ids = [chunk.chunk_id for chunk in selected]
    gold_ids = set(task.gold_chunk_ids)
    hit_count = sum(1 for chunk_id in selected_ids if chunk_id in gold_ids)
    recall = hit_count / len(gold_ids) if gold_ids else 1.0
    exact_hit = gold_ids.issubset(set(selected_ids))
    if task.task_type == "multi_hop_spread":
        answer_correct = exact_hit
    else:
        answer_correct = recall > 0.0
    return VariantResult(
        variant=variant,
        budget_k=budget_k,
        selected_chunk_ids=selected_ids,
        support_recall=recall,
        exact_support_hit=exact_hit,
        answer_correct=answer_correct,
    )


def run_indexer_vs_attention_matrix(
    *,
    variants: list[str] | None = None,
    budgets: list[int] | None = None,
) -> dict[str, Any]:
    tasks = build_indexer_vs_attention_cases()
    variants = variants or [
        "fuller_context_baseline",
        "window_plus_anchor",
        "sparse_indexer_lexical",
        "sparse_indexer_mixed",
        "sparse_indexer_structured",
        "compressed_attention_reference",
    ]
    budgets = budgets or [1, 2, 3]
    rows: list[TaskVariantRow] = []
    for task in tasks:
        for variant in variants:
            for budget in budgets:
                rows.append(
                    TaskVariantRow(
                        task_id=task.task_id,
                        task_type=task.task_type,
                        budget_class=task.budget_class,
                        result=evaluate_variant(task, variant=variant, budget_k=budget),
                    )
                )

    summary: dict[str, dict[str, Any]] = {}
    for variant in variants:
        variant_rows = [row for row in rows if row.result.variant == variant]
        budgets_seen = sorted({row.result.budget_k for row in variant_rows})
        summary[variant] = {
            "mean_support_recall": sum(row.result.support_recall for row in variant_rows) / len(variant_rows),
            "mean_answer_accuracy": sum(1.0 if row.result.answer_correct else 0.0 for row in variant_rows) / len(variant_rows),
            "budgets": budgets_seen,
        }

    diagnostics = [
        {
            "task_id": task.task_id,
            "structured_ranking": explain_variant_ranking(task, variant="sparse_indexer_structured")[:3],
            "mixed_ranking": explain_variant_ranking(task, variant="sparse_indexer_mixed")[:3],
        }
        for task in tasks
    ]

    return {
        "task_count": len(tasks),
        "tasks": [task.to_dict() for task in tasks],
        "rows": [row.to_dict() for row in rows],
        "summary": summary,
        "diagnostics": diagnostics,
    }


def render_indexer_vs_attention_markdown(report: dict[str, Any]) -> str:
    lines = ["# Indexer vs Attention Report", ""]
    lines.append("## Summary")
    lines.append("")
    lines.append("| Variant | Mean Support Recall | Mean Answer Accuracy | Budgets |")
    lines.append("|---|---:|---:|---|")
    for variant, stats in report["summary"].items():
        lines.append(
            f"| `{variant}` | {stats['mean_support_recall']:.3f} | "
            f"{stats['mean_answer_accuracy']:.3f} | {', '.join(str(b) for b in stats['budgets'])} |"
        )
    lines.append("")
    lines.append("## Rows")
    lines.append("")
    lines.append("| Task | Variant | Budget | Recall | Exact Hit | Answer Correct |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for row in report["rows"]:
        result = row["result"]
        lines.append(
            f"| `{row['task_id']}` | `{result['variant']}` | {result['budget_k']} | "
            f"{result['support_recall']:.3f} | {str(result['exact_support_hit']).lower()} | "
            f"{str(result['answer_correct']).lower()} |"
        )
    lines.append("")
    lines.append("## Structured Indexer Diagnostics")
    lines.append("")
    for diagnostic in report.get("diagnostics", []):
        lines.append(f"### `{diagnostic['task_id']}`")
        lines.append("")
        lines.append("| Variant | Chunk | Role | Score | Why It Ranked |")
        lines.append("|---|---|---|---:|---|")
        for variant_name in ["structured_ranking", "mixed_ranking"]:
            label = "sparse_indexer_structured" if variant_name == "structured_ranking" else "sparse_indexer_mixed"
            for row in diagnostic[variant_name]:
                reason = ", ".join(
                    f"{key}={value:.2f}"
                    for key, value in row.get("breakdown", {}).items()
                    if value > 0.0
                ) or "score-only"
                lines.append(
                    f"| `{label}` | `{row['chunk_id']}` ({row['path']}) | `{row['role']}` | "
                    f"{row['score']:.2f} | {reason} |"
                )
        lines.append("")
    return "\n".join(lines) + "\n"
