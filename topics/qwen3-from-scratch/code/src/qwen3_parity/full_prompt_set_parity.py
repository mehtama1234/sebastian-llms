from __future__ import annotations

import argparse
import json
from pathlib import Path

from qwen3_parity.prefix_logits_parity import (
    DEFAULT_URL,
    _build_official_config,
    _default_artifact_dir,
    _load_or_fetch_official_state,
)

FIXED_PROMPT_SET: tuple[str, ...] = (
    "Hello world.",
    "The capital of France is",
    "Write a Python function that returns the factorial of n.",
    "Roses are red,\nViolets are blue,",
    "Summarize this sentence in three words: attention improves sequence modeling.",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare scratch and official Qwen3 logits across a fixed prompt set."
    )
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--model-id", default="Qwen/Qwen3-0.6B")
    parser.add_argument("--layers", type=int, default=28)
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
    parser.add_argument(
        "--artifact-name",
        default="qwen3_0_6b_fixed_prompt_set_parity.json",
        help="Filename for the JSON artifact written under artifact-dir.",
    )
    return parser


def _tokenize_prompt_set(model_id: str, prompts: tuple[str, ...]) -> list[dict[str, object]]:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    items: list[dict[str, object]] = []
    for index, prompt in enumerate(prompts):
        encoded = tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
        input_ids = encoded["input_ids"]
        items.append(
            {
                "prompt_index": index,
                "prompt_text": prompt,
                "input_ids": input_ids,
                "token_count": int(input_ids.shape[1]),
            }
        )
    return items


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

    prompt_items = _tokenize_prompt_set(args.model_id, FIXED_PROMPT_SET)

    prompt_results: list[dict[str, object]] = []
    allclose = True
    global_max_abs_diff = 0.0
    global_mean_abs_diff = 0.0

    with torch.no_grad():
        for item in prompt_items:
            input_ids = item["input_ids"]
            scratch_logits = scratch_model(input_ids)
            official_logits = official_model(
                input_ids=input_ids,
                use_cache=False,
            ).logits

            max_abs_diff = (scratch_logits - official_logits).abs().max().item()
            mean_abs_diff = (scratch_logits - official_logits).abs().mean().item()
            prompt_allclose = torch.allclose(
                scratch_logits,
                official_logits,
                atol=args.atol,
                rtol=args.rtol,
            )

            prompt_results.append(
                {
                    "prompt_index": item["prompt_index"],
                    "prompt_text": item["prompt_text"],
                    "token_count": item["token_count"],
                    "input_ids": input_ids.squeeze(0).tolist(),
                    "max_abs_diff": max_abs_diff,
                    "mean_abs_diff": mean_abs_diff,
                    "allclose": prompt_allclose,
                }
            )
            allclose = allclose and prompt_allclose
            global_max_abs_diff = max(global_max_abs_diff, max_abs_diff)
            global_mean_abs_diff = max(global_mean_abs_diff, mean_abs_diff)

    artifact_path = Path(args.artifact_dir) / args.artifact_name
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "date": "2026-08-09",
        "model_id": args.model_id,
        "layers": args.layers,
        "prompt_count": len(prompt_results),
        "cache_hit": cache_hit,
        "cache_path": str(cache_path),
        "loaded_count": scratch_result.loaded_count,
        "missing_official": list(scratch_result.missing_official_keys),
        "missing_scratch": list(scratch_result.missing_scratch_keys),
        "global_max_abs_diff": global_max_abs_diff,
        "global_mean_abs_diff": global_mean_abs_diff,
        "allclose": allclose,
        "prompts": prompt_results,
    }
    artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("PROMPT_SET_PARITY_LAYERS", args.layers)
    print("PROMPT_SET_PARITY_PROMPTS", len(prompt_results))
    print("PROMPT_SET_PARITY_CACHE_HIT", cache_hit)
    print("PROMPT_SET_PARITY_CACHE_PATH", cache_path)
    print("PROMPT_SET_PARITY_ARTIFACT", artifact_path)
    print("PROMPT_SET_PARITY_LOADED", scratch_result.loaded_count)
    print("PROMPT_SET_PARITY_MISSING_OFFICIAL", len(scratch_result.missing_official_keys))
    print("PROMPT_SET_PARITY_MISSING_SCRATCH", len(scratch_result.missing_scratch_keys))
    print("PROMPT_SET_PARITY_MAX_ABS_DIFF", global_max_abs_diff)
    print("PROMPT_SET_PARITY_MAX_MEAN_ABS_DIFF", global_mean_abs_diff)
    print("PROMPT_SET_PARITY_ALLCLOSE", allclose)

    if not allclose:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
