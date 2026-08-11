from __future__ import annotations

import argparse
import json
from pathlib import Path

from .cli import _fmt_scorecard_table
from .experiment import run_experiment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="llm-dev-scorecard",
        description="Print production scorecards for every harness config in the default sweep.",
    )
    parser.add_argument("--out", type=Path, help="write scorecards as JSON to this path")
    args = parser.parse_args(argv)

    report = run_experiment()
    print(_fmt_scorecard_table(report.scorecards))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        payload = {name: sc.to_dict() for name, sc in report.scorecards.items()}
        args.out.write_text(json.dumps(payload, indent=2))
        print(f"\nwrote scorecards to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
