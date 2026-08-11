from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .summary import build_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize architecture experiment configs.")
    parser.add_argument("--config", required=True, help="Path to a model config JSON file.")
    parser.add_argument("--artifact", required=False, help="Optional JSON artifact output path.")
    parser.add_argument("--stdout", action="store_true", help="Print the summary JSON to stdout.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)
    summary = build_summary(config)

    if args.artifact:
        artifact_path = Path(args.artifact)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(summary, indent=2) + "\n")

    if args.stdout or not args.artifact:
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
