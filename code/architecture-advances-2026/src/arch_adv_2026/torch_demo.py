from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .torch_model import check_torch, run_torch_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a tiny torch demo for an architecture config.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--artifact", required=False)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--seq-len", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> None:
    availability = check_torch()
    if not availability.available:
        raise SystemExit(availability.reason)

    args = build_parser().parse_args()
    result = run_torch_demo(
        load_config(args.config),
        batch_size=args.batch_size,
        seq_len=args.seq_len,
        seed=args.seed,
    )
    if args.artifact:
        artifact_path = Path(args.artifact)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(result, indent=2) + "\n")
    if args.stdout or not args.artifact:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
