from __future__ import annotations

import argparse
import json
from pathlib import Path

from .training_report import generate_training_report, load_default_training_report_configs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a comparison report across current micro variants for training stability.")
    parser.add_argument("--root-dir", required=True)
    parser.add_argument("--artifact", required=False)
    parser.add_argument(
        "--variant",
        dest="variants",
        action="append",
        help="Limit the report to one or more variant labels. Can be passed multiple times.",
    )
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--seq-len", type=int, default=8)
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--clip-grad-norm", type=float, default=1.0)
    parser.add_argument("--report-runs", type=int, default=1)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    baseline, variants = load_default_training_report_configs(
        args.root_dir,
        variant_names=args.variants,
    )
    report = generate_training_report(
        baseline,
        variants,
        batch_size=args.batch_size,
        seq_len=args.seq_len,
        steps=args.steps,
        lr=args.lr,
        seed=args.seed,
        clip_grad_norm=args.clip_grad_norm,
        report_runs=args.report_runs,
    )

    if args.artifact:
        artifact_path = Path(args.artifact)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if args.stdout or not args.artifact:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
