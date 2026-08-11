from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_REFERENCE = "artifacts/reference/qwen3_0_6b_reference_snapshot.json"
DEFAULT_SCRATCH = "artifacts/scratch/qwen3_0_6b_scratch_config.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare reference and scratch Qwen3 config snapshots."
    )
    parser.add_argument("--reference", default=DEFAULT_REFERENCE)
    parser.add_argument("--scratch", default=DEFAULT_SCRATCH)
    return parser


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    args = build_parser().parse_args()
    reference = _load_json(args.reference)
    scratch = _load_json(args.scratch)

    ignored = {"generated_at_utc", "snapshot_kind", "tokenizer_class", "config_class", "model_class", "parameter_count", "parameter_count_non_embedding", "torch_version", "transformers_version"}
    keys = sorted((set(reference) | set(scratch)) - ignored)

    mismatches: list[tuple[str, object, object]] = []
    for key in keys:
        left = reference.get(key)
        right = scratch.get(key)
        if left != right:
            mismatches.append((key, left, right))

    if not mismatches:
        print("Config parity check passed")
        return 0

    print("Config parity check found mismatches:")
    for key, left, right in mismatches:
        print(f"- {key}: reference={left!r} scratch={right!r}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
