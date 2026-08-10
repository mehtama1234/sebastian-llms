from __future__ import annotations

import argparse
from qwen3_parity.remote_safetensors import (
    fetch_safetensors_header,
    fetch_safetensors_header_length,
    fetch_safetensors_tensor,
)


DEFAULT_URL = "https://huggingface.co/Qwen/Qwen3-0.6B/resolve/main/model.safetensors"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a bounded subset of real Qwen3 tensors and load them into a partial scratch receiver."
    )
    parser.add_argument("--url", default=DEFAULT_URL)
    return parser


def main() -> int:
    import torch

    from qwen3_parity.load_weights import load_official_weights_into_scratch
    from qwen3_parity.scratch.partial import (
        StructuralSliceReceiver,
        build_structural_slice_mapping,
    )

    args = build_parser().parse_args()

    header = fetch_safetensors_header(args.url)
    header_len = fetch_safetensors_header_length(args.url)

    mapping = build_structural_slice_mapping()
    official_state = {}
    for entry in mapping:
        official_state[entry.official_key] = fetch_safetensors_tensor(
            args.url,
            header_len=header_len,
            entry=header[entry.official_key],
        )

    receiver = StructuralSliceReceiver()
    result = load_official_weights_into_scratch(receiver, official_state, mapping=mapping)

    receiver_state = receiver.state_dict()
    exact_matches = 0
    for entry in mapping:
        if torch.equal(receiver_state[entry.scratch_key], official_state[entry.official_key]):
            exact_matches += 1

    print("REAL_SUBSET_KEYS", len(mapping))
    print("REAL_SUBSET_LOADED", result.loaded_count)
    print("REAL_SUBSET_MISSING_OFFICIAL", len(result.missing_official_keys))
    print("REAL_SUBSET_MISSING_SCRATCH", len(result.missing_scratch_keys))
    print("REAL_SUBSET_EXACT_MATCHES", exact_matches)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
