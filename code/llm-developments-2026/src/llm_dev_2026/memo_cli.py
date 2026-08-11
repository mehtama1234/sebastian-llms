from __future__ import annotations

import argparse
from pathlib import Path

from .experiment import run_experiment
from .memo import generate_memo, render_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="llm-dev-memo",
        description="Generate the adoption decision memo from the default harness sweep.",
    )
    parser.add_argument("--out", type=Path, help="write the memo markdown to this path")
    args = parser.parse_args(argv)

    report = run_experiment()
    memo = generate_memo(report)
    markdown = render_markdown(memo)
    print(markdown)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(markdown)
        print(f"wrote memo to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
