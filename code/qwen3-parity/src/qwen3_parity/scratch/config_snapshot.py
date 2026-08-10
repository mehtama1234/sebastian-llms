from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from qwen3_parity.scratch.config import QWEN3_0_6B_CONFIG


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write the local scratch-side Qwen3 0.6B config snapshot."
    )
    parser.add_argument(
        "--artifact-dir",
        default="artifacts/scratch",
        help="Directory where the JSON snapshot should be written.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the JSON snapshot to stdout after writing it.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    payload = QWEN3_0_6B_CONFIG.to_dict()
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    payload["snapshot_kind"] = "scratch-config"

    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "qwen3_0_6b_scratch_config.json"
    artifact_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote scratch config snapshot to {artifact_path}")
    if args.stdout:
        print(json.dumps(payload, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
