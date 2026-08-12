from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark_loader import load_benchmark_manifest
from .real_benchmark_runtime import format_real_benchmark_summary, run_real_benchmark_readiness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="llm-dev-real-benchmark",
        description="Load a real benchmark manifest and audit whether the local workspace is ready to run it.",
    )
    parser.add_argument("manifest", type=Path, help="path to a benchmark manifest JSON file")
    parser.add_argument("--out", type=Path, help="write the JSON readiness report to this path")
    parser.add_argument("--quiet", action="store_true", help="suppress the human-readable summary")
    args = parser.parse_args(argv)

    manifest = load_benchmark_manifest(args.manifest)
    report = run_real_benchmark_readiness(manifest)

    if not args.quiet:
        print(format_real_benchmark_summary(report))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report.to_dict(), indent=2))
        if not args.quiet:
            print(f"\nwrote readiness report to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
