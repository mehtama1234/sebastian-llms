from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def generate_compressed_attention_promotion_memo(
    assessment: dict[str, Any],
    stress_assessment: dict[str, Any] | None = None,
    speed_tail_assessment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    recommendation = assessment["recommendation"]
    gates = assessment["gates"]
    training = assessment["training"]
    benchmark = assessment["benchmark"]
    long_context = assessment["long_context"]

    summary_lines = [
        f"Promotion recommendation: `{recommendation}` for `{assessment['variant']}`.",
        f"Gate state: long-context `{str(bool(gates['long_context_pass'])).lower()}`, training `{str(bool(gates['training_pass'])).lower()}`, systems `{str(bool(gates['benchmark_pass'])).lower()}`.",
        f"Long-context proxy quality delta vs baseline: `{long_context['quality_delta_vs_baseline']:.3f}` with KV saving ratio `{long_context['kv_cache_saving_ratio_vs_baseline']:.3f}`.",
        f"Training mean loss delta vs baseline: `{training['final_loss_delta_vs_baseline_mean']:.3f}` with range `{training['final_loss_delta_vs_baseline_range']:.3f}`.",
        f"Systems mean runtime ratio: `{benchmark['mean_ratio_across_grid']:.3f}`; worst runtime ratio: `{benchmark['worst_ratio_across_grid']:.3f}`.",
    ]
    if stress_assessment is not None:
        summary_lines.append(
            f"Focused stress follow-up reproduces failure: `{str(bool(stress_assessment['reproduces_failure'])).lower()}`; "
            f"slow-tail persists: `{str(bool(stress_assessment['speed_instability'])).lower()}`."
        )
    if speed_tail_assessment is not None:
        worst_tail_batch = max(
            speed_tail_assessment["batch_summaries"],
            key=lambda row: (row["worst_speed_ratio"], row["mean_speed_ratio"]),
        )
        widest_slow_batch = max(
            speed_tail_assessment["batch_summaries"],
            key=lambda row: (row["slow_row_fraction"], row["mean_speed_ratio"]),
        )
        dominant_steps = speed_tail_assessment["dominant_steps"]
        summary_lines.append(
            f"Short-context speed tail: broadest slow-row concentration at batch `{widest_slow_batch['batch_size']}` "
            f"(slow fraction `{widest_slow_batch['slow_row_fraction']:.3f}`), but worst tail at batch `{worst_tail_batch['batch_size']}` "
            f"with worst speed ratio `{worst_tail_batch['worst_speed_ratio']:.3f}` and step slice `{dominant_steps['steps']}`."
        )

    if recommendation == "promote":
        recommendations = [
            "Promote `compressed_attention` to the next heavier experiment stage.",
            "Treat the current promotion evidence as sufficient across long-context, training, and systems surfaces.",
            "Use the validated promotion pass as the default evidence refresh path before heavier-stage reruns.",
        ]
    else:
        recommendations = [
            "Keep `compressed_attention` as the default carry-forward candidate rather than promoting it yet.",
            "Treat the failed gates as the next concrete work queue instead of reopening the whole architecture search.",
        ]
        if not gates["training_pass"]:
            if stress_assessment is not None and stress_assessment.get("reproduces_failure"):
                recommendations.append(
                    "Treat the short-context training weakness as real, not just noisy, because the focused stress rerun reproduces it."
                )
            else:
                recommendations.append(
                    "Prioritize a broader training schedule follow-up because training evidence is still the limiting surface."
                )
        if not gates["benchmark_pass"]:
            recommendations.append(
                "Recheck worst-case systems behavior on an even broader grid before promotion."
            )
        if not gates["long_context_pass"]:
            recommendations.append(
                "Harden the long-context evaluation set before promotion because proxy quality is not yet strong enough."
            )
        if stress_assessment is not None and stress_assessment.get("speed_instability"):
            recommendations.append(
                "Focus the next training investigation on the short-context speed tail because the stress rerun still shows repeated slow rows."
            )
        if speed_tail_assessment is not None:
            widest_slow_batch = max(
                speed_tail_assessment["batch_summaries"],
                key=lambda row: (row["slow_row_fraction"], row["mean_speed_ratio"]),
            )
            dominant_steps = speed_tail_assessment["dominant_steps"]
            recommendations.append(
                f"Treat batch `{widest_slow_batch['batch_size']}` as the broad slowdown slice and `{dominant_steps['steps']}` steps as the worst tail slice in the next training investigation."
            )

    return {
        "headline": "Compressed attention promotion memo",
        "date": assessment["date"],
        "variant": assessment["variant"],
        "recommendation": recommendation,
        "summary_lines": summary_lines,
        "recommendations": recommendations,
        "signals": assessment.get("signals", []),
        "risks": assessment.get("risks", []),
        "gates": gates,
        "stress_assessment_available": stress_assessment is not None,
        "stress_assessment": stress_assessment,
        "speed_tail_assessment_available": speed_tail_assessment is not None,
        "speed_tail_assessment": speed_tail_assessment,
    }


def render_compressed_attention_promotion_memo_markdown(memo: dict[str, Any]) -> str:
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
    lines.append("## Positive Signals")
    for line in memo["signals"]:
        lines.append(f"- {line}")
    lines.append("")
    lines.append("## Risks")
    for line in memo["risks"]:
        lines.append(f"- {line}")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a compact promotion memo from the compressed_attention promotion assessment.")
    parser.add_argument("--assessment", required=True)
    parser.add_argument("--stress-assessment", required=False)
    parser.add_argument("--speed-tail-assessment", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    assessment = load_json(args.assessment)
    stress_assessment = load_json(args.stress_assessment) if args.stress_assessment else None
    speed_tail_assessment = load_json(args.speed_tail_assessment) if args.speed_tail_assessment else None
    memo = generate_compressed_attention_promotion_memo(assessment, stress_assessment, speed_tail_assessment)
    markdown = render_compressed_attention_promotion_memo_markdown(memo)

    if args.artifact_json:
        json_path = Path(args.artifact_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(
                {
                    "memo": memo,
                    "assessment": assessment,
                    "stress_assessment": stress_assessment,
                    "speed_tail_assessment": speed_tail_assessment,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    if args.artifact_md:
        md_path = Path(args.artifact_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
    if args.stdout or (not args.artifact_md and not args.artifact_json):
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
