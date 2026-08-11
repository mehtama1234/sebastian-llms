from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import compare_numeric_benchmarks
from .config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark baseline vs variant numeric demos.")
    parser.add_argument("--baseline-config", required=True)
    parser.add_argument("--variant-config", required=True)
    parser.add_argument("--artifact", required=False)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--seq-len", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--warmup-runs", type=int, default=1)
    parser.add_argument("--measured-runs", type=int, default=5)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = compare_numeric_benchmarks(
        load_config(args.baseline_config),
        load_config(args.variant_config),
        batch_size=args.batch_size,
        seq_len=args.seq_len,
        seed=args.seed,
        warmup_runs=args.warmup_runs,
        measured_runs=args.measured_runs,
    )

    if args.artifact:
        artifact_path = Path(args.artifact)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(result, indent=2) + "\n")

    if args.stdout or not args.artifact:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
