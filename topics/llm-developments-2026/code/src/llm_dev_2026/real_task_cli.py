from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark_loader import load_benchmark_manifest
from .config import InstructionMode
from .provider import build_provider
from .runtime import run_real_task


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="llm-dev-real-task",
        description="Run one real benchmark task through the local runtime/provider seam and emit an attempt artifact.",
    )
    parser.add_argument("manifest", type=Path, help="path to a benchmark manifest JSON file")
    parser.add_argument("task_id", help="task id to execute")
    parser.add_argument(
        "--instruction-mode",
        choices=[mode.value for mode in InstructionMode],
        default=InstructionMode.NONE.value,
        help="instruction loading mode for the task runtime",
    )
    parser.add_argument(
        "--provider",
        choices=["local", "openai"],
        default="local",
        help="provider backend to use for the attempt artifact",
    )
    parser.add_argument(
        "--retrieval-mode",
        choices=["lexical", "sparse", "task_aware"],
        default="task_aware",
        help="retrieval mode to use when evidence_source is retrieval",
    )
    parser.add_argument(
        "--evidence-source",
        choices=["gold", "retrieval"],
        default="gold",
        help="whether to use gold evidence spans or runtime retrieval",
    )
    parser.add_argument(
        "--model",
        default="gpt-5.6",
        help="model name for the OpenAI-backed provider",
    )
    parser.add_argument(
        "--api-key-env",
        default="OPENAI_API_KEY",
        help="environment variable that holds the OpenAI API key",
    )
    parser.add_argument("--out", type=Path, help="write the attempt artifact as JSON")
    args = parser.parse_args(argv)

    manifest = load_benchmark_manifest(args.manifest)
    provider = build_provider(args.provider, model=args.model, api_key_env=args.api_key_env)
    artifact = run_real_task(
        manifest,
        args.task_id,
        provider,
        instruction_mode=InstructionMode(args.instruction_mode),
        evidence_source=args.evidence_source,
        retrieval_mode=args.retrieval_mode,
    )

    payload = artifact.to_dict()
    print(json.dumps(payload, indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
