from __future__ import annotations

import argparse
import json
from pathlib import Path

from .real_policy_experiment import run_real_policy_experiment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="llm-dev-real-policy-experiment",
        description="Run the default real-task policy matrix and compare scorecards across configurations.",
    )
    parser.add_argument("manifest", type=Path, help="path to a benchmark manifest JSON file")
    parser.add_argument("--task-class", help="optional task_class filter")
    parser.add_argument("--difficulty", help="optional difficulty filter")
    parser.add_argument("--long-context", choices=["true", "false"], help="optional long_context filter")
    parser.add_argument("--out", type=Path, help="write the full policy experiment report as JSON")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    long_context = None
    if args.long_context is not None:
        long_context = args.long_context == "true"

    report = run_real_policy_experiment(
        str(args.manifest),
        task_class=args.task_class,
        difficulty=args.difficulty,
        long_context=long_context,
    )
    payload = report.to_dict()
    if not args.quiet:
        print(json.dumps(payload["scorecards"], indent=2))
        print(json.dumps(payload["comparisons"], indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
