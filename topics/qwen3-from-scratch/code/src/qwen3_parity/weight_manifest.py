from __future__ import annotations

import argparse
import json
from pathlib import Path

from qwen3_parity.scratch.config import QWEN3_0_6B_CONFIG
from qwen3_parity.weight_map import build_weight_mapping


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write the expected scratch-side loaded tensor manifest for Qwen3 0.6B."
    )
    parser.add_argument(
        "--artifact-dir",
        default="artifacts/mapping",
        help="Directory where the JSON manifest should be written.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the manifest JSON to stdout after writing it.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    mapping = build_weight_mapping(QWEN3_0_6B_CONFIG)
    scratch_keys = [entry.scratch_key for entry in mapping]
    official_keys = [entry.official_key for entry in mapping]
    payload = {
        "model_id": QWEN3_0_6B_CONFIG.model_id,
        "expected_official_keys": official_keys,
        "expected_scratch_keys": scratch_keys,
        "num_expected_keys": len(mapping),
    }

    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "qwen3_0_6b_weight_manifest.json"
    artifact_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote weight manifest to {artifact_path}")
    if args.stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
