from __future__ import annotations

import argparse
import json
from pathlib import Path

from .training_benchmark import compare_torch_training_benchmarks, load_config_pair


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark baseline vs variant tiny Torch training stability.")
    parser.add_argument("--baseline-config", required=True)
    parser.add_argument("--variant-config", required=True)
    parser.add_argument("--artifact", required=False)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seq-len", type=int, default=16)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--clip-grad-norm", type=float, default=1.0)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    baseline, variant = load_config_pair(args.baseline_config, args.variant_config)
    result = compare_torch_training_benchmarks(
        baseline,
        variant,
        batch_size=args.batch_size,
        seq_len=args.seq_len,
        steps=args.steps,
        lr=args.lr,
        seed=args.seed,
        clip_grad_norm=args.clip_grad_norm,
    )

    if args.artifact:
        artifact_path = Path(args.artifact)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    if args.stdout or not args.artifact:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
