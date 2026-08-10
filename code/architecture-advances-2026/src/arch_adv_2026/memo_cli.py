from __future__ import annotations

import argparse
import json
from pathlib import Path

from .memo import generate_decision_memo, render_decision_memo_markdown
from .report import generate_variant_report, load_default_report_configs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a markdown decision memo from the variant report.")
    parser.add_argument("--root-dir", required=True)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--seq-len", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--warmup-runs", type=int, default=1)
    parser.add_argument("--measured-runs", type=int, default=5)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    baseline, variants = load_default_report_configs(args.root_dir)
    report = generate_variant_report(
        baseline,
        variants,
        batch_size=args.batch_size,
        seq_len=args.seq_len,
        seed=args.seed,
        warmup_runs=args.warmup_runs,
        measured_runs=args.measured_runs,
    )
    memo = generate_decision_memo(report)
    markdown = render_decision_memo_markdown(memo, report)

    if args.artifact_json:
        json_path = Path(args.artifact_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps({"memo": memo, "report": report}, indent=2) + "\n")

    if args.artifact_md:
        md_path = Path(args.artifact_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown)

    if args.stdout or (not args.artifact_md and not args.artifact_json):
        print(markdown)


if __name__ == "__main__":
    main()
