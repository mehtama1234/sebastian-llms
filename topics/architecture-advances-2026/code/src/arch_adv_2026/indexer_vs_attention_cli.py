from __future__ import annotations

import argparse
import json
from pathlib import Path

from arch_adv_2026.indexer_vs_attention import (
    render_indexer_vs_attention_markdown,
    run_indexer_vs_attention_matrix,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate synthetic indexer-vs-attention comparison artifacts."
    )
    parser.add_argument("--artifact-json", required=True)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--budgets", nargs="+", type=int, default=[1, 2, 3])
    parser.add_argument("--stdout", action="store_true")
    return parser


def write_json_artifact(report: dict, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return output_path


def write_markdown_artifact(markdown: str, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def main() -> int:
    args = build_parser().parse_args()
    report = run_indexer_vs_attention_matrix(budgets=args.budgets)
    markdown = render_indexer_vs_attention_markdown(report)
    json_path = write_json_artifact(report, args.artifact_json)
    print(f"Wrote indexer-vs-attention JSON artifact to {json_path}")
    if args.artifact_md:
        markdown_path = write_markdown_artifact(markdown, args.artifact_md)
        print(f"Wrote indexer-vs-attention markdown artifact to {markdown_path}")
    if args.stdout or not args.artifact_md:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
