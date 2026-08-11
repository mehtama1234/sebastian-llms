from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_URL = "https://huggingface.co/Qwen/Qwen3-0.6B/resolve/main/model.safetensors"


def _default_artifact_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "artifacts" / "parity"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare scratch and official Qwen3 prefix-model logits on the same real weight slice."
    )
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--layers", type=int, default=1)
    parser.add_argument("--seq-len", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--atol", type=float, default=1e-5)
    parser.add_argument("--rtol", type=float, default=1e-5)
    parser.add_argument(
        "--artifact-dir",
        default=str(_default_artifact_dir()),
        help="Directory for cached official slices and parity outputs.",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Re-fetch the official tensor slice even if a local cache exists.",
    )
    return parser


def _build_official_config(prefix_config):
    from transformers.models.qwen3.configuration_qwen3 import Qwen3Config

    return Qwen3Config(
        vocab_size=prefix_config.vocab_size,
        hidden_size=prefix_config.hidden_size,
        intermediate_size=prefix_config.intermediate_size,
        num_hidden_layers=prefix_config.num_hidden_layers,
        num_attention_heads=prefix_config.num_attention_heads,
        num_key_value_heads=prefix_config.num_key_value_heads,
        head_dim=prefix_config.head_dim,
        hidden_act=prefix_config.hidden_act,
        max_position_embeddings=prefix_config.max_position_embeddings,
        max_window_layers=prefix_config.max_window_layers,
        rms_norm_eps=prefix_config.rms_norm_eps,
        attention_bias=prefix_config.attention_bias,
        attention_dropout=prefix_config.attention_dropout,
        use_cache=prefix_config.use_cache,
        use_sliding_window=prefix_config.use_sliding_window,
        sliding_window=prefix_config.sliding_window,
        tie_word_embeddings=prefix_config.tie_word_embeddings,
        bos_token_id=prefix_config.bos_token_id,
        eos_token_id=prefix_config.eos_token_id,
        rope_parameters=prefix_config.rope_scaling,
    )


def _fetch_official_state(url: str, mapping) -> dict[str, "torch.Tensor"]:
    from qwen3_parity.remote_safetensors import (
        fetch_safetensors_header,
        fetch_safetensors_header_length,
        fetch_safetensors_tensor,
    )

    header = fetch_safetensors_header(url)
    header_len = fetch_safetensors_header_length(url)

    official_state = {}
    for entry in mapping:
        official_state[entry.official_key] = fetch_safetensors_tensor(
            url,
            header_len=header_len,
            entry=header[entry.official_key],
        )
    return official_state


def _slice_cache_path(artifact_dir: str, layers: int) -> Path:
    return Path(artifact_dir) / f"qwen3_0_6b_prefix_{layers}l_state.pt"


def _load_or_fetch_official_state(
    *,
    url: str,
    mapping,
    artifact_dir: str,
    layers: int,
    refresh_cache: bool,
) -> tuple[dict[str, "torch.Tensor"], bool, Path]:
    import torch

    cache_path = _slice_cache_path(artifact_dir, layers)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if cache_path.exists() and not refresh_cache:
        payload = torch.load(cache_path, map_location="cpu")
        return payload["official_state"], True, cache_path

    official_state = _fetch_official_state(url, mapping)
    torch.save(
        {
            "model_id": "Qwen/Qwen3-0.6B",
            "layers": layers,
            "official_keys": [entry.official_key for entry in mapping],
            "official_state": official_state,
        },
        cache_path,
    )
    return official_state, False, cache_path


def _build_prompt(prefix_config, seq_len: int) -> "torch.Tensor":
    import torch

    if seq_len < 2:
        raise ValueError(f"seq_len must be at least 2, got {seq_len}")

    middle_len = seq_len - 2
    middle = torch.arange(17, 17 + middle_len, dtype=torch.long)
    return torch.cat(
        (
            torch.tensor([prefix_config.bos_token_id], dtype=torch.long),
            middle,
            torch.tensor([prefix_config.eos_token_id], dtype=torch.long),
        )
    ).unsqueeze(0)


def main() -> int:
    import torch
    from transformers.models.qwen3.modeling_qwen3 import Qwen3ForCausalLM

    from qwen3_parity.load_weights import load_official_weights_into_scratch
    from qwen3_parity.scratch.config import build_prefix_test_config
    from qwen3_parity.scratch.model import Qwen3ScratchModel
    from qwen3_parity.weight_map import build_weight_mapping

    args = build_parser().parse_args()

    torch.manual_seed(args.seed)

    prefix_config = build_prefix_test_config(args.layers)
    mapping = build_weight_mapping(prefix_config)
    official_state, cache_hit, cache_path = _load_or_fetch_official_state(
        url=args.url,
        mapping=mapping,
        artifact_dir=args.artifact_dir,
        layers=args.layers,
        refresh_cache=args.refresh_cache,
    )

    scratch_model = Qwen3ScratchModel(prefix_config).eval()
    scratch_result = load_official_weights_into_scratch(
        scratch_model,
        official_state,
        mapping=mapping,
    )

    official_config = _build_official_config(prefix_config)
    official_config._attn_implementation = "eager"
    official_model = Qwen3ForCausalLM(official_config).eval()
    official_model.load_state_dict(official_state, strict=True)

    input_ids = _build_prompt(prefix_config, args.seq_len)

    with torch.no_grad():
        scratch_logits = scratch_model(input_ids)
        official_logits = official_model(
            input_ids=input_ids,
            use_cache=False,
        ).logits

    max_abs_diff = (scratch_logits - official_logits).abs().max().item()
    mean_abs_diff = (scratch_logits - official_logits).abs().mean().item()
    allclose = torch.allclose(
        scratch_logits,
        official_logits,
        atol=args.atol,
        rtol=args.rtol,
    )

    print("PREFIX_PARITY_LAYERS", args.layers)
    print("PREFIX_PARITY_SEQ_LEN", args.seq_len)
    print("PREFIX_PARITY_CACHE_HIT", cache_hit)
    print("PREFIX_PARITY_CACHE_PATH", cache_path)
    print("PREFIX_PARITY_LOADED", scratch_result.loaded_count)
    print("PREFIX_PARITY_MISSING_OFFICIAL", len(scratch_result.missing_official_keys))
    print("PREFIX_PARITY_MISSING_SCRATCH", len(scratch_result.missing_scratch_keys))
    print("PREFIX_PARITY_MAX_ABS_DIFF", max_abs_diff)
    print("PREFIX_PARITY_MEAN_ABS_DIFF", mean_abs_diff)
    print("PREFIX_PARITY_ALLCLOSE", allclose)

    if not allclose:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
