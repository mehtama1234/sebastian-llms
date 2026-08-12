from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a machine-readable selector artifact from an indexer-vs-attention report."
    )
    parser.add_argument("--artifact", required=True, help="Path to indexer_vs_attention.json")
    parser.add_argument("--selector-out", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def load_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _rows_for_budget(report: dict[str, Any], budget_k: int) -> list[dict[str, Any]]:
    return [row for row in report["rows"] if row["result"]["budget_k"] == budget_k]


def _aggregate_variant_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    variants = sorted({row["result"]["variant"] for row in rows})
    aggregated: list[dict[str, Any]] = []
    for variant in variants:
        variant_rows = [row for row in rows if row["result"]["variant"] == variant]
        accuracy = sum(1.0 if row["result"]["answer_correct"] else 0.0 for row in variant_rows) / len(variant_rows)
        recall = sum(row["result"]["support_recall"] for row in variant_rows) / len(variant_rows)
        exact_hit_rate = (
            sum(1.0 if row["result"]["exact_support_hit"] else 0.0 for row in variant_rows) / len(variant_rows)
        )
        aggregated.append(
            {
                "variant": variant,
                "mean_answer_accuracy": accuracy,
                "mean_support_recall": recall,
                "mean_exact_hit_rate": exact_hit_rate,
                "task_count": len(variant_rows),
            }
        )
    return aggregated


def _best_variant(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(
        rows,
        key=lambda row: (
            row["mean_answer_accuracy"],
            row["mean_support_recall"],
            row["mean_exact_hit_rate"],
            row["variant"] == "sparse_indexer_structured",
        ),
        reverse=True,
    )[0]


def _hard_task_rows(report: dict[str, Any], budget_k: int) -> list[dict[str, Any]]:
    hard_types = {"multi_hop_spread", "synonym_bridge", "verifier_chain"}
    return [
        row for row in report["rows"] if row["result"]["budget_k"] == budget_k and row["task_type"] in hard_types
    ]


def build_indexer_vs_attention_selector(report: dict[str, Any]) -> dict[str, Any]:
    budgets = sorted({row["result"]["budget_k"] for row in report["rows"]})
    smallest_budget = min(budgets)
    medium_budget = budgets[min(1, len(budgets) - 1)]

    smallest_budget_rows = _aggregate_variant_rows(_rows_for_budget(report, smallest_budget))
    medium_budget_rows = _aggregate_variant_rows(_rows_for_budget(report, medium_budget))
    hard_task_budget_rows = _aggregate_variant_rows(_hard_task_rows(report, medium_budget))

    return {
        "source_report_task_count": report["task_count"],
        "selection_policy": {
            "smallest_budget": smallest_budget,
            "medium_budget": medium_budget,
            "hard_task_types": ["multi_hop_spread", "synonym_bridge", "verifier_chain"],
            "tie_break_order": [
                "mean_answer_accuracy",
                "mean_support_recall",
                "mean_exact_hit_rate",
                "prefer_sparse_indexer_structured_on_remaining_ties",
            ],
        },
        "recommendations": {
            "tight_budget": _best_variant(smallest_budget_rows),
            "medium_budget": _best_variant(medium_budget_rows),
            "hard_tasks_medium_budget": _best_variant(hard_task_budget_rows),
        },
        "budget_tables": {
            "tight_budget": smallest_budget_rows,
            "medium_budget": medium_budget_rows,
            "hard_tasks_medium_budget": hard_task_budget_rows,
        },
        "notes": [
            "This selector turns the synthetic report into explicit chunk-selection recommendations.",
            "Hard-task rows isolate multi-hop, synonym-bridge, and verifier-chain cases where shallow overlap is less trustworthy.",
            "The selector is still synthetic; use it to guide the next heavier retrieval experiment rather than as final proof.",
        ],
    }


def write_json_artifact(data: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    args = build_parser().parse_args()
    report = load_report(args.artifact)
    selector = build_indexer_vs_attention_selector(report)
    if args.selector_out:
        path = write_json_artifact(selector, args.selector_out)
        print(f"Wrote indexer-vs-attention selector to {path}")
    if args.stdout or not args.selector_out:
        print(json.dumps(selector, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
