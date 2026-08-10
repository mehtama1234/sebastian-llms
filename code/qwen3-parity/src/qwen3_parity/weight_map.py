from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from qwen3_parity.scratch.config import QWEN3_0_6B_CONFIG, Qwen3DenseConfig


@dataclass(frozen=True)
class WeightMappingEntry:
    official_key: str
    scratch_key: str


def build_weight_mapping(
    config: Qwen3DenseConfig = QWEN3_0_6B_CONFIG,
) -> list[WeightMappingEntry]:
    mapping: list[WeightMappingEntry] = [
        WeightMappingEntry("model.embed_tokens.weight", "embed_tokens.weight"),
        WeightMappingEntry("model.norm.weight", "norm.weight"),
        WeightMappingEntry("lm_head.weight", "lm_head.weight"),
    ]

    for layer_idx in range(config.num_hidden_layers):
        prefix = f"model.layers.{layer_idx}"
        scratch_prefix = f"layers.{layer_idx}"
        mapping.extend(
            [
                WeightMappingEntry(
                    f"{prefix}.input_layernorm.weight",
                    f"{scratch_prefix}.input_layernorm.weight",
                ),
                WeightMappingEntry(
                    f"{prefix}.post_attention_layernorm.weight",
                    f"{scratch_prefix}.post_attention_layernorm.weight",
                ),
                WeightMappingEntry(
                    f"{prefix}.self_attn.q_proj.weight",
                    f"{scratch_prefix}.self_attn.q_proj.weight",
                ),
                WeightMappingEntry(
                    f"{prefix}.self_attn.k_proj.weight",
                    f"{scratch_prefix}.self_attn.k_proj.weight",
                ),
                WeightMappingEntry(
                    f"{prefix}.self_attn.k_norm.weight",
                    f"{scratch_prefix}.self_attn.k_norm.weight",
                ),
                WeightMappingEntry(
                    f"{prefix}.self_attn.q_norm.weight",
                    f"{scratch_prefix}.self_attn.q_norm.weight",
                ),
                WeightMappingEntry(
                    f"{prefix}.self_attn.v_proj.weight",
                    f"{scratch_prefix}.self_attn.v_proj.weight",
                ),
                WeightMappingEntry(
                    f"{prefix}.self_attn.o_proj.weight",
                    f"{scratch_prefix}.self_attn.o_proj.weight",
                ),
                WeightMappingEntry(
                    f"{prefix}.mlp.gate_proj.weight",
                    f"{scratch_prefix}.mlp.gate_proj.weight",
                ),
                WeightMappingEntry(
                    f"{prefix}.mlp.up_proj.weight",
                    f"{scratch_prefix}.mlp.up_proj.weight",
                ),
                WeightMappingEntry(
                    f"{prefix}.mlp.down_proj.weight",
                    f"{scratch_prefix}.mlp.down_proj.weight",
                ),
            ]
        )

    return mapping


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write the expected official-to-scratch Qwen3 weight mapping."
    )
    parser.add_argument(
        "--artifact-dir",
        default="artifacts/mapping",
        help="Directory where the JSON mapping should be written.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the mapping JSON to stdout after writing it.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    mapping = build_weight_mapping()
    payload = {
        "model_id": QWEN3_0_6B_CONFIG.model_id,
        "num_entries": len(mapping),
        "entries": [asdict(entry) for entry in mapping],
    }

    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "qwen3_0_6b_weight_map.json"
    artifact_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote weight mapping to {artifact_path}")
    if args.stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
