from __future__ import annotations

import argparse

DEFAULT_URL = "https://huggingface.co/Qwen/Qwen3-0.6B/resolve/main/model.safetensors"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare scratch and official Qwen3 layer-0 forward outputs on the same real weight slice."
    )
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--seq-len", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--atol", type=float, default=1e-5)
    parser.add_argument("--rtol", type=float, default=1e-5)
    return parser


def _build_official_config():
    from transformers.models.qwen3.configuration_qwen3 import Qwen3Config

    from qwen3_parity.scratch.config import QWEN3_0_6B_CONFIG

    return Qwen3Config(
        vocab_size=QWEN3_0_6B_CONFIG.vocab_size,
        hidden_size=QWEN3_0_6B_CONFIG.hidden_size,
        intermediate_size=QWEN3_0_6B_CONFIG.intermediate_size,
        num_hidden_layers=QWEN3_0_6B_CONFIG.num_hidden_layers,
        num_attention_heads=QWEN3_0_6B_CONFIG.num_attention_heads,
        num_key_value_heads=QWEN3_0_6B_CONFIG.num_key_value_heads,
        head_dim=QWEN3_0_6B_CONFIG.head_dim,
        hidden_act=QWEN3_0_6B_CONFIG.hidden_act,
        max_position_embeddings=QWEN3_0_6B_CONFIG.max_position_embeddings,
        max_window_layers=QWEN3_0_6B_CONFIG.max_window_layers,
        rms_norm_eps=QWEN3_0_6B_CONFIG.rms_norm_eps,
        attention_bias=QWEN3_0_6B_CONFIG.attention_bias,
        attention_dropout=QWEN3_0_6B_CONFIG.attention_dropout,
        use_cache=QWEN3_0_6B_CONFIG.use_cache,
        use_sliding_window=QWEN3_0_6B_CONFIG.use_sliding_window,
        sliding_window=QWEN3_0_6B_CONFIG.sliding_window,
        tie_word_embeddings=QWEN3_0_6B_CONFIG.tie_word_embeddings,
        bos_token_id=QWEN3_0_6B_CONFIG.bos_token_id,
        eos_token_id=QWEN3_0_6B_CONFIG.eos_token_id,
        rope_parameters=QWEN3_0_6B_CONFIG.rope_scaling,
    )


def _fetch_official_state(url: str) -> dict[str, "torch.Tensor"]:
    from qwen3_parity.remote_safetensors import (
        fetch_safetensors_header,
        fetch_safetensors_header_length,
        fetch_safetensors_tensor,
    )
    from qwen3_parity.scratch.partial import build_layer0_structural_mapping

    header = fetch_safetensors_header(url)
    header_len = fetch_safetensors_header_length(url)

    official_state = {}
    for entry in build_layer0_structural_mapping():
        official_state[entry.official_key] = fetch_safetensors_tensor(
            url,
            header_len=header_len,
            entry=header[entry.official_key],
        )
    return official_state


def _build_official_layer_state(official_state: dict[str, "torch.Tensor"]) -> dict[str, "torch.Tensor"]:
    prefix = "model.layers.0."
    return {
        key.removeprefix(prefix): value
        for key, value in official_state.items()
        if key.startswith(prefix)
    }


def _build_scratch_layer_mapping():
    from qwen3_parity.scratch.partial import build_layer0_structural_mapping
    from qwen3_parity.weight_map import WeightMappingEntry

    prefix = "layers.0."
    return [
        WeightMappingEntry(
            entry.official_key,
            entry.scratch_key.removeprefix(prefix),
        )
        for entry in build_layer0_structural_mapping()
    ]


def main() -> int:
    import torch
    from transformers.models.qwen3.modeling_qwen3 import Qwen3DecoderLayer, Qwen3RotaryEmbedding

    from qwen3_parity.load_weights import load_official_weights_into_scratch
    from qwen3_parity.scratch.config import QWEN3_0_6B_CONFIG
    from qwen3_parity.scratch.layers import (
        Qwen3DecoderLayer as ScratchDecoderLayer,
        build_rope_cache,
    )
    from qwen3_parity.scratch.model import build_causal_mask
    from qwen3_parity.scratch.partial import build_layer0_structural_mapping

    args = build_parser().parse_args()

    torch.manual_seed(args.seed)

    official_state = _fetch_official_state(args.url)

    scratch_layer = ScratchDecoderLayer(QWEN3_0_6B_CONFIG).eval()
    scratch_result = load_official_weights_into_scratch(
        scratch_layer,
        official_state,
        mapping=_build_scratch_layer_mapping(),
    )

    official_config = _build_official_config()
    official_config._attn_implementation = "eager"
    official_layer = Qwen3DecoderLayer(official_config, layer_idx=0).eval()
    official_layer.load_state_dict(_build_official_layer_state(official_state), strict=True)
    rotary = Qwen3RotaryEmbedding(official_config)

    hidden_states = torch.randn(
        1,
        args.seq_len,
        official_config.hidden_size,
        dtype=torch.float32,
    )
    position_ids = torch.arange(args.seq_len, dtype=torch.long).unsqueeze(0)
    attention_mask = build_causal_mask(args.seq_len).to(dtype=torch.float32)
    position_embeddings = rotary(hidden_states, position_ids)

    scratch_rope_cache = build_rope_cache(
        head_dim=scratch_layer.self_attn.head_dim,
        max_position_embeddings=official_config.max_position_embeddings,
        rope_theta=official_config.rope_parameters["rope_theta"],
        device=hidden_states.device,
    )

    with torch.no_grad():
        scratch_output = scratch_layer(
            hidden_states,
            rope_cache=scratch_rope_cache,
            attention_mask=attention_mask,
            offset=0,
        )
        official_output = official_layer(
            hidden_states,
            attention_mask=attention_mask,
            position_ids=position_ids,
            position_embeddings=position_embeddings,
            use_cache=False,
        )

    max_abs_diff = (scratch_output - official_output).abs().max().item()
    mean_abs_diff = (scratch_output - official_output).abs().mean().item()
    allclose = torch.allclose(
        scratch_output,
        official_output,
        atol=args.atol,
        rtol=args.rtol,
    )

    print("LAYER0_PARITY_SEQ_LEN", args.seq_len)
    print("LAYER0_PARITY_LOADED", scratch_result.loaded_count)
    print("LAYER0_PARITY_MISSING_OFFICIAL", len(scratch_result.missing_official_keys))
    print("LAYER0_PARITY_MISSING_SCRATCH", len(scratch_result.missing_scratch_keys))
    print("LAYER0_PARITY_MAX_ABS_DIFF", max_abs_diff)
    print("LAYER0_PARITY_MEAN_ABS_DIFF", mean_abs_diff)
    print("LAYER0_PARITY_ALLCLOSE", allclose)

    if not allclose:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
