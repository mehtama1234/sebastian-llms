from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MICRO_RATIO_TIE_TOLERANCE = 0.02


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _rows_by_variant(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["variant"]: row for row in report["variant_rows"]}


def _runtime_pick(rows: dict[str, dict[str, Any]]) -> str:
    return min(rows.values(), key=lambda row: row["mean_ratio_vs_baseline_mean"])["variant"]


def _memory_pick(rows: dict[str, dict[str, Any]]) -> str:
    return min(rows.values(), key=lambda row: row["estimated_kv_cache_bytes"])["variant"]


def _runtime_leaders(
    rows: dict[str, dict[str, Any]],
    *,
    tolerance: float = MICRO_RATIO_TIE_TOLERANCE,
) -> list[str]:
    best = min(row["mean_ratio_vs_baseline_mean"] for row in rows.values())
    return sorted(
        row["variant"]
        for row in rows.values()
        if row["mean_ratio_vs_baseline_mean"] <= best + tolerance
    )


def _memory_leaders(rows: dict[str, dict[str, Any]]) -> list[str]:
    lowest = min(row["estimated_kv_cache_bytes"] for row in rows.values())
    return sorted(row["variant"] for row in rows.values() if row["estimated_kv_cache_bytes"] == lowest)


def _long_context_pick(selector: dict[str, Any]) -> str:
    return selector["recommendations"]["quality_preserving_memory"]["variant_kind"]


def _stable_training_pick(
    rows: dict[str, dict[str, Any]],
    *,
    metric_key: str,
    consistent_key: str,
    range_key: str,
) -> str | None:
    stable_rows = [row for row in rows.values() if row.get(consistent_key, False)]
    if not stable_rows:
        return None
    return min(
        stable_rows,
        key=lambda row: (
            row[metric_key],
            row.get(range_key, 0.0),
            -row.get("lowest_final_loss_delta_win_rate", 0.0),
            -row.get("fastest_step_win_rate", 0.0),
        ),
    )["variant"]


def _training_summary(training: dict[str, Any]) -> dict[str, Any]:
    if "variant_trends" in training:
        rows = {row["variant"]: row for row in training["variant_trends"]}
        fastest = min(rows.values(), key=lambda row: row["mean_step_ms_ratio_vs_baseline_mean"])
        lowest_loss = min(rows.values(), key=lambda row: row["final_loss_delta_vs_baseline_mean"])
        most_stable_grad = min(rows.values(), key=lambda row: row["max_grad_norm_delta_vs_baseline_mean"])
        stable_fastest_variant = _stable_training_pick(
            rows,
            metric_key="mean_step_ms_ratio_vs_baseline_mean",
            consistent_key="consistent_speed_advantage",
            range_key="mean_step_ms_ratio_vs_baseline_range",
        )
        stable_lowest_loss_variant = _stable_training_pick(
            rows,
            metric_key="final_loss_delta_vs_baseline_mean",
            consistent_key="consistent_loss_advantage",
            range_key="final_loss_delta_vs_baseline_range",
        )
        finite_rows = [row["variant"] for row in training["variant_trends"] if row["all_matrix_rows_finite"]]
        winner_counts = training.get("winner_counts", {})
        return {
            "mode": "matrix",
            "row_count": len(training["rows"]),
            "trend_row_count": len(training["variant_trends"]),
            "fastest_variant": fastest["variant"],
            "lowest_final_loss_delta_variant": lowest_loss["variant"],
            "lowest_grad_norm_delta_variant": most_stable_grad["variant"],
            "stable_fastest_variant": stable_fastest_variant,
            "stable_lowest_final_loss_delta_variant": stable_lowest_loss_variant,
            "all_finite_variants": finite_rows,
            "rows": rows,
            "seq_lens": training.get("seq_lens", []),
            "steps_list": training.get("steps_list", []),
            "seeds": training.get("seeds", []),
            "winner_counts": winner_counts,
        }
    if "variant_rows" in training:
        rows = {row["variant"]: row for row in training["variant_rows"]}
        fastest = min(rows.values(), key=lambda row: row["mean_step_ms_ratio_vs_baseline_mean"])
        lowest_loss = min(rows.values(), key=lambda row: row["final_loss_delta_vs_baseline_mean"])
        finite_rows = [row["variant"] for row in training["variant_rows"] if row["all_runs_finite"]]
        return {
            "mode": "report",
            "row_count": len(training["variant_rows"]),
            "fastest_variant": fastest["variant"],
            "lowest_final_loss_delta_variant": lowest_loss["variant"],
            "all_finite_variants": finite_rows,
            "rows": rows,
        }
    baseline = training["baseline"]["summary"]
    variant = training["variant"]["summary"]
    comparison = training["comparison"]
    return {
        "mode": "single_benchmark",
        "variant": training["variant"]["variant"],
        "baseline_variant": training["baseline"]["variant"],
        "both_all_steps_finite": comparison["both_all_steps_finite"],
        "final_loss_delta": comparison["final_loss_delta"],
        "loss_improvement_ratio_delta": comparison["loss_improvement_ratio_delta"],
        "mean_step_ms_ratio_variant_over_baseline": comparison["mean_step_ms_ratio_variant_over_baseline"],
        "max_grad_norm_delta": comparison["max_grad_norm_delta"],
        "baseline_final_loss": baseline["final_loss"],
        "variant_final_loss": variant["final_loss"],
    }


def _review_summary(review_plan: dict[str, Any] | None) -> dict[str, Any] | None:
    if not review_plan:
        return None
    rows = {row["variant"]: row for row in review_plan.get("rows", [])}
    return {
        "priority_variants": review_plan.get("summary", {}).get("priority_variants", []),
        "raw_mismatch_variants": review_plan.get("summary", {}).get(
            "raw_mismatch_variants",
            review_plan.get("summary", {}).get("mismatch_variants", []),
        ),
        "resolved_mismatch_variants": review_plan.get("summary", {}).get("resolved_mismatch_variants", []),
        "unresolved_mismatch_variants": review_plan.get("summary", {}).get("unresolved_mismatch_variants", []),
        "rows": rows,
    }


def _benchmark_summary(benchmark_matrix: dict[str, Any] | None) -> dict[str, Any] | None:
    if not benchmark_matrix:
        return None
    rows = {row["variant"]: row for row in benchmark_matrix.get("variant_summary_rows", [])}
    summary = benchmark_matrix.get("summary", {})
    baseline = benchmark_matrix.get("baseline", {})
    return {
        "best_mean_runtime_variant": summary.get("best_mean_runtime_variant"),
        "best_mean_runtime_variants": summary.get("best_mean_runtime_variants", []),
        "best_worst_case_runtime_variant": summary.get("best_worst_case_runtime_variant"),
        "best_worst_case_runtime_variants": summary.get("best_worst_case_runtime_variants", []),
        "lowest_kv_variant": summary.get("lowest_kv_variant"),
        "lowest_kv_variants": summary.get("lowest_kv_variants", []),
        "grid_cell_count": summary.get("grid_cell_count"),
        "baseline": baseline,
        "rows": rows,
    }


def _leader_text(variants: list[str], fallback: str | None) -> str:
    names = variants or ([fallback] if fallback else [])
    if not names:
        return "unavailable"
    if len(names) == 1:
        return f"`{names[0]}`"
    return "tie between " + ", ".join(f"`{variant}`" for variant in names)


def _subset_benchmark_leaders(
    benchmark: dict[str, Any] | None,
    variants: list[str],
) -> dict[str, list[str]] | None:
    if not benchmark:
        return None
    subset_rows = [benchmark["rows"][variant] for variant in variants if variant in benchmark["rows"]]
    if not subset_rows:
        return None
    mean_best = min(row["mean_ratio_across_grid"] for row in subset_rows)
    worst_best = min(row["worst_ratio_across_grid"] for row in subset_rows)
    kv_values = [
        row["estimated_kv_cache_bytes"]
        for row in subset_rows
        if row.get("estimated_kv_cache_bytes") is not None
    ]
    return {
        "best_mean_runtime_variants": sorted(
            row["variant"] for row in subset_rows if row["mean_ratio_across_grid"] <= mean_best + 0.01
        ),
        "best_worst_case_runtime_variants": sorted(
            row["variant"] for row in subset_rows if row["worst_ratio_across_grid"] <= worst_best + 0.01
        ),
        "lowest_kv_variants": (
            sorted(
                row["variant"]
                for row in subset_rows
                if row.get("estimated_kv_cache_bytes") is not None and row["estimated_kv_cache_bytes"] == min(kv_values)
            )
            if kv_values
            else []
        ),
    }


def _supports_runtime_secondary_pick(variant: str, benchmark: dict[str, Any] | None) -> bool:
    if not benchmark:
        return True
    row = benchmark["rows"].get(variant)
    if not row:
        return True
    return row["mean_ratio_across_grid"] <= 1.0 and row["worst_ratio_across_grid"] <= 1.2


def _apply_review_overrides(
    *,
    keep_secondary: list[str],
    explore: list[str],
    review: dict[str, Any] | None,
) -> tuple[list[str], list[str], list[str]]:
    notes: list[str] = []
    if not review:
        return keep_secondary, explore, notes

    secondary = list(keep_secondary)
    exploratory = list(explore)
    for variant in list(secondary):
        review_row = review["rows"].get(variant)
        if not review_row:
            continue
        if review_row.get("followup_mixed_but_current_favored") is True:
            notes.append(
                f"Focused follow-up review keeps `{variant}` secondary because the weighted evidence still favors the current label, even though a weaker surface points toward `{review_row.get('followup_candidate_decision', review_row.get('suggested_decision', 'exploratory'))}`."
            )
            continue
        if review_row.get("followup_conflicting_directions") is True:
            notes.append(
                f"Focused follow-up review keeps `{variant}` secondary for now because the current surfaces conflict on whether it should stay secondary or move to exploratory."
            )
            continue
        if review_row.get("suggested_decision") == "exploratory":
            secondary.remove(variant)
            if variant not in exploratory:
                exploratory.append(variant)
            notes.append(
                f"Focused follow-up review demotes `{variant}` from secondary to exploratory until the stronger evidence gap is resolved."
            )
    return secondary, exploratory, notes


def generate_final_decision_memo(
    micro_report: dict[str, Any],
    long_context_selector: dict[str, Any],
    long_context_execution: dict[str, Any],
    training_benchmark: dict[str, Any],
    review_plan: dict[str, Any] | None = None,
    benchmark_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = _rows_by_variant(micro_report)
    runtime_pick = _runtime_pick(rows)
    memory_pick = _memory_pick(rows)
    runtime_leaders = _runtime_leaders(rows)
    memory_leaders = _memory_leaders(rows)
    long_context_pick = _long_context_pick(long_context_selector)
    training = _training_summary(training_benchmark)
    review = _review_summary(review_plan)
    benchmark = _benchmark_summary(benchmark_matrix)

    keep_default = long_context_pick
    keep_secondary: list[str] = []
    explore: list[str] = []
    drop_for_now: list[str] = []

    if memory_pick != keep_default:
        keep_secondary.append(memory_pick)
    if (
        runtime_pick != keep_default
        and runtime_pick not in keep_secondary
        and _supports_runtime_secondary_pick(runtime_pick, benchmark)
    ):
        keep_secondary.append(runtime_pick)

    for variant in rows:
        if variant in {keep_default, *keep_secondary}:
            continue
        if variant in {"mhc", "history_compression"}:
            explore.append(variant)
        else:
            drop_for_now.append(variant)

    keep_secondary, explore, review_override_notes = _apply_review_overrides(
        keep_secondary=keep_secondary,
        explore=explore,
        review=review,
    )
    shortlist_benchmark = _subset_benchmark_leaders(benchmark, [keep_default, *keep_secondary])

    focused_compare = long_context_execution.get("focused_compare_summary", {})
    selected_bucket = focused_compare.get("selected_bucket")
    baseline_bucket = focused_compare.get("baseline_bucket")
    proxy_quality_delta = focused_compare.get("proxy_quality_delta")
    kv_saving_ratio = long_context_execution["delta"]["kv_cache_saving_ratio_vs_baseline"]
    default_review_row = review["rows"].get(keep_default) if review else None
    default_under_review = bool(default_review_row and default_review_row.get("priority", 0) >= 2)

    summary_lines = [
        (
            f"Default carry-forward architecture: `{keep_default}` (provisional; still flagged for follow-up review)."
            if default_under_review
            else f"Default carry-forward architecture: `{keep_default}`."
        ),
        f"Best micro runtime direction: {_leader_text(runtime_leaders, runtime_pick)}.",
        f"Best micro KV-memory direction: {_leader_text(memory_leaders, memory_pick)}.",
        (
            f"Best mean systems-sweep runtime direction among carry-forward candidates: "
            f"{_leader_text(shortlist_benchmark.get('best_mean_runtime_variants', []), benchmark['best_mean_runtime_variant'])}; "
            f"best worst-case systems-sweep direction among carry-forward candidates: "
            f"{_leader_text(shortlist_benchmark.get('best_worst_case_runtime_variants', []), benchmark['best_worst_case_runtime_variant'])}; "
            f"lowest-KV systems-sweep direction among carry-forward candidates: "
            f"{_leader_text(shortlist_benchmark.get('lowest_kv_variants', []), benchmark['lowest_kv_variant'])}."
            if benchmark and shortlist_benchmark
            else "Systems-sweep benchmark matrix is unavailable."
        ),
        f"Longest-context proxy selector carry-forward pick: `{long_context_pick}`.",
        (
            f"Focused long-context proxy rerun for `{keep_default}` kept all cases passing while trading "
            f"{kv_saving_ratio:.3f} KV-cache saving ratio against a proxy-quality delta of `{proxy_quality_delta:.3f}`."
            if selected_bucket and baseline_bucket and proxy_quality_delta is not None
            else "Focused long-context proxy rerun summary is unavailable."
        ),
        (
            (
                (
                    f"Training matrix fastest trend variant: `{training['fastest_variant']}`; "
                    f"lowest final-loss trend variant: `{training['lowest_final_loss_delta_variant']}`; "
                    f"lowest grad-delta trend variant: `{training['lowest_grad_norm_delta_variant']}`; "
                    f"stable speed leader: `{training['stable_fastest_variant'] or 'none'}`; "
                    f"stable loss leader: `{training['stable_lowest_final_loss_delta_variant'] or 'none'}`; "
                    f"finite across matrix: {', '.join(f'`{variant}`' for variant in training['all_finite_variants'])}."
                )
                if training["mode"] == "matrix"
                else f"Training report fastest step-time variant: `{training['fastest_variant']}`; "
                f"lowest final-loss delta variant: `{training['lowest_final_loss_delta_variant']}`; "
                f"finite variants: {', '.join(f'`{variant}`' for variant in training['all_finite_variants'])}."
            )
            if training["mode"] in {"report", "matrix"}
            else (
                f"Training-stability proxy for `{training['variant']}` stayed finite and ran at "
                f"{training['mean_step_ms_ratio_variant_over_baseline']:.3f}x baseline step time, "
                f"with final loss delta `{training['final_loss_delta']:.3f}`."
            )
        ),
    ]
    if review and review["priority_variants"]:
        summary_lines.append(
            "Focused follow-up review priority variants: "
            + ", ".join(f"`{variant}`" for variant in review["priority_variants"])
            + "."
        )
    if review and review["unresolved_mismatch_variants"]:
        summary_lines.append(
            "Active unresolved decision mismatches still needing review: "
            + ", ".join(f"`{variant}`" for variant in review["unresolved_mismatch_variants"])
            + "."
        )

    recommendations = []
    default_prefix = "Keep"
    if default_under_review:
        default_prefix = "Keep provisionally"
    if runtime_pick == keep_default:
        recommendations.append(
            f"{default_prefix} `{keep_default}` as the default next heavier experiment candidate because it is the current long-context carry-forward winner and also the fastest micro runtime direction."
        )
    else:
        recommendations.append(
            f"{default_prefix} `{keep_default}` as the default next heavier experiment candidate because it is the current long-context carry-forward winner and the strongest blended quality-preserving systems trade."
        )
    if keep_secondary:
        recommendations.append(
            "Keep secondary branches for "
            + ", ".join(f"`{variant}`" for variant in keep_secondary)
            + " when the decision is dominated by a single constraint rather than the blended objective."
        )
    if benchmark:
        default_benchmark_row = benchmark["rows"].get(keep_default)
        if default_benchmark_row:
            recommendations.append(
                f"Use the systems sweep as a second systems gate: `{keep_default}` currently averages "
                f"{default_benchmark_row['mean_ratio_across_grid']:.3f}x baseline across the sampled micro grid, "
                f"with worst cell `{default_benchmark_row['worst_ratio_across_grid']:.3f}`."
            )
        for variant in keep_secondary:
            benchmark_row = benchmark["rows"].get(variant)
            if benchmark_row and benchmark_row["worst_ratio_across_grid"] > 1.2:
                recommendations.append(
                    f"Do not promote `{variant}` beyond secondary until its systems-sweep worst cell drops below about 1.2x baseline or its quality gain clearly justifies the instability."
                )
    if "mhc" in explore:
        recommendations.append(
            "Keep `mhc` exploratory only until a real quality benchmark shows enough gain to justify its higher complexity and no KV-memory win."
        )
    if "history_compression" in explore:
        recommendations.append(
            "Keep `history_compression` exploratory for explicitly old-token-dominated long-context work, not as the default path."
        )
    if drop_for_now:
        recommendations.append(
            "Do not carry forward "
            + ", ".join(f"`{variant}`" for variant in drop_for_now)
            + " as default candidates with current evidence."
        )
    if training["mode"] == "single_benchmark":
        recommendations.append(
            "Before any full adoption call, expand the training-stability benchmark beyond the current compressed-attention run so the same evidence exists for the other shortlisted variants."
        )
    elif training["mode"] == "report":
        recommendations.append(
            "Use the new training report as a gate: any variant that stops staying finite or develops clearly worse final-loss deltas should fall out of the carry-forward set."
        )
    else:
        recommendations.append(
            "Use the training matrix as a stronger gate: prefer variants that stay finite across schedule/seed combinations and avoid variants whose win disappears under small training-shape changes."
        )
        if training.get("stable_lowest_final_loss_delta_variant"):
            recommendations.append(
                f"Use repeated and consistent training wins as a filter: the current stable loss leader is `{training['stable_lowest_final_loss_delta_variant']}`."
            )
        if training.get("stable_fastest_variant"):
            recommendations.append(
                f"Treat stable speed wins separately from mean speed wins: the current stable speed leader is `{training['stable_fastest_variant']}`."
            )
        if training["winner_counts"]:
            loss_wins = training["winner_counts"].get("lowest_final_loss_delta", {})
            if loss_wins:
                loss_leader = max(loss_wins.items(), key=lambda item: item[1])[0]
                recommendations.append(
                    f"Treat repeated matrix wins as stronger evidence than a single row: the current loss-trend leader is `{loss_leader}`."
                )
    if review and "kv_sharing" in review["priority_variants"]:
        kv_review = review["rows"].get("kv_sharing")
        if kv_review:
            if kv_review.get("followup_mixed_but_current_favored") is True:
                recommendations.append(
                    "Treat `kv_sharing` as a bounded secondary branch rather than a fully settled keep: follow-up evidence is mixed, but the weighted balance still favors `secondary` over `exploratory`."
                )
            elif kv_review.get("followup_conflicting_directions") is True:
                recommendations.append(
                    "Treat `kv_sharing` as an explicit review item rather than a settled secondary keep: the focused training and long-context follow-ups disagree on whether it should stay `secondary` or move to `exploratory`."
                )
            else:
                recommendations.append(
                    f"Treat `kv_sharing` as an explicit review item rather than a settled secondary keep: the focused follow-up currently points toward `{kv_review['suggested_decision']}`."
                )
    recommendations.extend(review_override_notes)

    evidence_matrix = []
    for variant, row in sorted(rows.items()):
        evidence_matrix.append(
            {
                "variant": variant,
                "micro_runtime_ratio_vs_baseline": row["mean_ratio_vs_baseline_mean"],
                "micro_kv_cache_bytes": row["estimated_kv_cache_bytes"],
                "benchmark_mean_ratio_across_grid": (
                    benchmark["rows"].get(variant, {}).get("mean_ratio_across_grid")
                    if benchmark
                    else None
                ),
                "benchmark_worst_ratio_across_grid": (
                    benchmark["rows"].get(variant, {}).get("worst_ratio_across_grid")
                    if benchmark
                    else None
                ),
                "selected_by_long_context_proxy": variant == long_context_pick,
                "selected_by_micro_runtime": variant == runtime_pick,
                "selected_by_micro_memory": variant == memory_pick,
                "has_training_evidence": (
                    variant in training["rows"]
                    if training["mode"] in {"report", "matrix"}
                    else variant == training["variant"]
                ),
            }
        )

    return {
        "headline": "Architecture Advances 2026 Final Decision Memo",
        "date": "2026-08-09",
        "default_carry_forward_variant": keep_default,
        "secondary_variants": keep_secondary,
        "exploratory_variants": explore,
        "drop_for_now_variants": drop_for_now,
        "summary_lines": summary_lines,
        "recommendations": recommendations,
        "evidence": {
            "micro_report_baseline": micro_report["baseline"],
            "micro_runtime_leaders": runtime_leaders,
            "micro_memory_leaders": memory_leaders,
            "long_context_selection_policy": long_context_selector["selection_policy"],
            "long_context_focused_compare_summary": focused_compare,
            "training_summary": training,
            "review_summary": review,
            "benchmark_summary": benchmark,
            "shortlist_benchmark_summary": shortlist_benchmark,
        },
        "evidence_matrix": evidence_matrix,
    }


def render_final_decision_memo_markdown(memo: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {memo['headline']}")
    lines.append("")
    lines.append(f"_Updated: {memo['date']}_")
    lines.append("")
    lines.append("## Bottom line")
    for line in memo["summary_lines"]:
        lines.append(f"- {line}")
    lines.append("")
    lines.append("## Recommendations")
    for line in memo["recommendations"]:
        lines.append(f"- {line}")
    lines.append("")
    lines.append("## Carry Forward")
    lines.append(f"- Default: `{memo['default_carry_forward_variant']}`")
    lines.append(
        "- Secondary: "
        + (", ".join(f"`{variant}`" for variant in memo["secondary_variants"]) if memo["secondary_variants"] else "none")
    )
    lines.append(
        "- Exploratory: "
        + (", ".join(f"`{variant}`" for variant in memo["exploratory_variants"]) if memo["exploratory_variants"] else "none")
    )
    lines.append(
        "- Drop for now: "
        + (", ".join(f"`{variant}`" for variant in memo["drop_for_now_variants"]) if memo["drop_for_now_variants"] else "none")
    )
    lines.append("")
    lines.append("## Evidence Matrix")
    lines.append("")
    lines.append("| Variant | Micro Runtime Ratio | Sweep Mean Ratio | Sweep Worst Ratio | Micro KV Bytes | Long-Context Pick | Runtime Pick | Memory Pick | Training Evidence |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in memo["evidence_matrix"]:
        sweep_mean = f"{row['benchmark_mean_ratio_across_grid']:.3f}" if row.get("benchmark_mean_ratio_across_grid") is not None else "n/a"
        sweep_worst = f"{row['benchmark_worst_ratio_across_grid']:.3f}" if row.get("benchmark_worst_ratio_across_grid") is not None else "n/a"
        lines.append(
            f"| `{row['variant']}` | {row['micro_runtime_ratio_vs_baseline']:.3f} | {sweep_mean} | {sweep_worst} | {row['micro_kv_cache_bytes']} | "
            f"{str(row['selected_by_long_context_proxy']).lower()} | {str(row['selected_by_micro_runtime']).lower()} | "
            f"{str(row['selected_by_micro_memory']).lower()} | {str(row['has_training_evidence']).lower()} |"
        )
    lines.append("")
    lines.append("## Evidence Notes")
    training = memo["evidence"]["training_summary"]
    review = memo["evidence"].get("review_summary")
    benchmark = memo["evidence"].get("benchmark_summary")
    if training["mode"] == "matrix":
        lines.append(
            "- Training matrix coverage: "
            f"seq_lens `{training['seq_lens']}`, steps `{training['steps_list']}`, seeds `{training['seeds']}`."
        )
        lines.append(
            "- Training evidence coverage: "
            + ", ".join(f"`{variant}`" for variant in sorted(training["rows"].keys()))
        )
        lines.append(
            f"- Matrix winners: fastest `{training['fastest_variant']}`, lowest final-loss delta `{training['lowest_final_loss_delta_variant']}`, lowest grad-delta `{training['lowest_grad_norm_delta_variant']}`."
        )
        lines.append(
            f"- Stable matrix leaders: speed `{training['stable_fastest_variant'] or 'none'}`, loss `{training['stable_lowest_final_loss_delta_variant'] or 'none'}`."
        )
        if training["winner_counts"]:
            lines.append(f"- Matrix winner counts: `{json.dumps(training['winner_counts'])}`")
    elif training["mode"] == "report":
        lines.append(
            "- Training evidence coverage: "
            + ", ".join(
                f"`{variant}`"
                for variant in sorted(training["rows"].keys())
            )
        )
        lines.append(
            f"- Training fastest step-time variant: `{training['fastest_variant']}`; lowest final-loss delta variant: `{training['lowest_final_loss_delta_variant']}`."
        )
    else:
        lines.append(
            f"- Training evidence currently exists for `{training['variant']}` only; both runs finite: `{training['both_all_steps_finite']}`."
        )
    if review and review["priority_variants"]:
        lines.append(
            "- Focused review priorities: "
            + ", ".join(f"`{variant}`" for variant in review["priority_variants"])
        )
    if review and review["raw_mismatch_variants"]:
        lines.append(
            "- Raw audit mismatches: "
            + ", ".join(f"`{variant}`" for variant in review["raw_mismatch_variants"])
        )
    if review and review["resolved_mismatch_variants"]:
        lines.append(
            "- Resolved mismatches via focused follow-up: "
            + ", ".join(f"`{variant}`" for variant in review["resolved_mismatch_variants"])
        )
    if review and review["unresolved_mismatch_variants"]:
        lines.append(
            "- Active unresolved mismatches: "
            + ", ".join(f"`{variant}`" for variant in review["unresolved_mismatch_variants"])
        )
    if benchmark:
        baseline = benchmark.get("baseline", {})
        lines.append(
            f"- Benchmark matrix coverage: batch sizes `{baseline.get('batch_sizes', [])}`, seq_lens `{baseline.get('seq_lens', [])}`, "
            f"grid cells `{benchmark.get('grid_cell_count')}`."
        )
        lines.append(
            f"- Benchmark matrix leaders: mean runtime {_leader_text(benchmark.get('best_mean_runtime_variants', []), benchmark.get('best_mean_runtime_variant'))}, "
            f"worst-case runtime {_leader_text(benchmark.get('best_worst_case_runtime_variants', []), benchmark.get('best_worst_case_runtime_variant'))}, "
            f"lowest KV {_leader_text(benchmark.get('lowest_kv_variants', []), benchmark.get('lowest_kv_variant'))}."
        )
    lines.append(
        f"- Focused long-context proxy compare summary: `{json.dumps(memo['evidence']['long_context_focused_compare_summary'])}`"
    )
    lines.append("")
    return "\n".join(lines)
