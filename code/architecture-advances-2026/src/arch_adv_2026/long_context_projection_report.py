from __future__ import annotations

import argparse
from pathlib import Path

from .long_context_projection import load_json, render_projection_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a markdown report from a long-context variant projection artifact.")
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--markdown-out", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    projection = load_json(args.artifact)
    markdown = render_projection_markdown(projection)
    if args.markdown_out:
        path = Path(args.markdown_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
        print(f"Wrote long-context projection report to {path}")
    if args.stdout or not args.markdown_out:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
