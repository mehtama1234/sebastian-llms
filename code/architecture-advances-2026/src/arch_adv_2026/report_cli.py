from __future__ import annotations

import argparse
import json
from pathlib import Path

from .report import generate_variant_report, load_default_report_configs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a comparison report across current micro variants.")
    parser.add_argument("--root-dir", required=True, help="Architecture workspace root directory.")
    parser.add_argument("--artifact", required=False)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--seq-len", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--warmup-runs", type=int, default=1)
    parser.add_argument("--measured-runs", type=int, default=5)
    parser.add_argument("--report-runs", type=int, default=3)
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
        report_runs=args.report_runs,
    )

    if args.artifact:
        artifact_path = Path(args.artifact)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(report, indent=2) + "\n")

    if args.stdout or not args.artifact:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
