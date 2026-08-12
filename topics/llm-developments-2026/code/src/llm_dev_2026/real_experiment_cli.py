from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import InstructionMode
from .real_experiment import run_real_experiment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="llm-dev-real-experiment",
        description="Run a real benchmark manifest through the runtime/provider/verifier stack and emit a scorecard report.",
    )
    parser.add_argument("manifest", type=Path, help="path to a benchmark manifest JSON file")
    parser.add_argument("--provider", choices=["local", "openai"], default="local")
    parser.add_argument("--model", default="gpt-5.6")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--evidence-source", choices=["gold", "retrieval"], default="gold")
    parser.add_argument("--retrieval-mode", choices=["lexical", "sparse", "task_aware"], default="task_aware")
    parser.add_argument("--retrieval-top-k", type=int, default=2)
    parser.add_argument("--evidence-selection", choices=["all", "first", "sparse"], default="all")
    parser.add_argument("--evidence-top-k", type=int, default=1)
    parser.add_argument(
        "--instruction-mode",
        choices=[mode.value for mode in InstructionMode],
        default=InstructionMode.NONE.value,
    )
    parser.add_argument("--task-class", help="optional task_class filter")
    parser.add_argument("--difficulty", help="optional difficulty filter")
    parser.add_argument("--long-context", choices=["true", "false"], help="optional long_context filter")
    parser.add_argument("--skip-validation", action="store_true")
    parser.add_argument("--out", type=Path, help="write the full report as JSON")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    long_context = None
    if args.long_context is not None:
        long_context = args.long_context == "true"

    report = run_real_experiment(
        str(args.manifest),
        provider_backend=args.provider,
        model=args.model,
        api_key_env=args.api_key_env,
        instruction_mode=InstructionMode(args.instruction_mode),
        evidence_source=args.evidence_source,
        retrieval_mode=args.retrieval_mode,
        retrieval_top_k=args.retrieval_top_k,
        evidence_selection=args.evidence_selection,
        evidence_top_k=args.evidence_top_k,
        run_validation_checks=not args.skip_validation,
        task_class=args.task_class,
        difficulty=args.difficulty,
        long_context=long_context,
    )
    payload = report.to_dict()
    if not args.quiet:
        print(json.dumps(payload["scorecard"], indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
