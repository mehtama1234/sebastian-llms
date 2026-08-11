from __future__ import annotations

import argparse
import json
from pathlib import Path

from .experiment import run_experiment


def _fmt_scorecard_table(scorecards: dict) -> str:
    header = f"{'config':<28}{'honest':>8}{'report':>8}{'halluc':>8}{'tokens':>8}{'ops':>8}{'att':>6}"
    rows = [header, "-" * len(header)]
    for name, sc in scorecards.items():
        rows.append(
            f"{name:<28}"
            f"{sc.task_success_rate:>8.2f}"
            f"{sc.reported_success_rate:>8.2f}"
            f"{sc.hallucination_rate:>8.2f}"
            f"{sc.mean_prompt_tokens_final:>8.0f}"
            f"{sc.mean_retrieval_ops:>8.0f}"
            f"{sc.mean_attempts:>6.1f}"
        )
    return "\n".join(rows)


def _fmt_comparisons(report) -> str:
    rows = ["", "comparisons (candidate vs baseline):"]
    for c in report.comparisons:
        axis = report.comparison_axis.get(f"{c.baseline}->{c.candidate}", "")
        rows.append(
            f"  [{axis:<18}] {c.candidate:<26} success {c.task_success_delta:+.2f}  "
            f"halluc {c.hallucination_delta:+.2f}  latency {c.latency_delta:+.0f}  -> {c.verdict}"
        )
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="llm-dev-experiment",
        description="Run the LLMDevelopments-2026 harness policy sweep and score every config.",
    )
    parser.add_argument("--out", type=Path, help="write the full JSON report to this path")
    parser.add_argument("--quiet", action="store_true", help="suppress the human-readable summary")
    args = parser.parse_args(argv)

    report = run_experiment()

    if not args.quiet:
        print(_fmt_scorecard_table(report.scorecards))
        print(_fmt_comparisons(report))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report.to_dict(), indent=2))
        if not args.quiet:
            print(f"\nwrote report to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
