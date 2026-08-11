from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a tiny scratch-model smoke test for Qwen3 parity code."
    )
    parser.add_argument(
        "--seq-len",
        type=int,
        default=4,
        help="Sequence length for the synthetic forward pass.",
    )
    return parser


def main() -> int:
    import torch

    from qwen3_parity.load_weights import load_official_weights_into_scratch
    from qwen3_parity.scratch.config import build_tiny_test_config
    from qwen3_parity.scratch.model import Qwen3ScratchModel
    from qwen3_parity.weight_map import build_weight_mapping

    args = build_parser().parse_args()

    config = build_tiny_test_config()
    model = Qwen3ScratchModel(config)
    mapping = build_weight_mapping(config)

    partial_state = {}
    for entry in mapping[:5]:
        partial_state[entry.official_key] = model.state_dict()[entry.scratch_key].clone()

    load_result = load_official_weights_into_scratch(model, partial_state)

    input_ids = torch.arange(args.seq_len).unsqueeze(0) % config.vocab_size
    logits = model(input_ids)

    print("SMOKE_MODEL_ID", config.model_id)
    print("SMOKE_LAYERS", config.num_hidden_layers)
    print("SMOKE_MAPPING_ENTRIES", len(mapping))
    print("SMOKE_LOADED_COUNT", load_result.loaded_count)
    print("SMOKE_MISSING_OFFICIAL", len(load_result.missing_official_keys))
    print("SMOKE_MISSING_SCRATCH", len(load_result.missing_scratch_keys))
    print("SMOKE_LOGITS_SHAPE", tuple(logits.shape))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
