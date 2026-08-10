from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MODEL_ID = "Qwen/Qwen3-0.6B"


@dataclass(slots=True)
class TransformersAvailability:
    available: bool
    reason: str | None = None


@dataclass(slots=True)
class ReferenceSnapshot:
    model_id: str
    architecture: str | None
    model_type: str | None
    transformers_version: str
    torch_version: str | None
    vocab_size: int | None
    hidden_size: int | None
    intermediate_size: int | None
    num_hidden_layers: int | None
    num_attention_heads: int | None
    num_key_value_heads: int | None
    head_dim: int | None
    hidden_act: str | None
    max_position_embeddings: int | None
    max_window_layers: int | None
    rms_norm_eps: float | None
    rope_theta: float | None
    rope_scaling: object | None
    attention_bias: bool | None
    attention_dropout: float | None
    use_cache: bool | None
    use_sliding_window: bool | None
    sliding_window: int | None
    tie_word_embeddings: bool | None
    bos_token_id: int | None
    eos_token_id: int | None
    torch_dtype: str | None
    parameter_count: int | None
    parameter_count_non_embedding: int | None
    tokenizer_class: str
    config_class: str
    model_class: str | None
    generated_at_utc: str


def check_transformers() -> TransformersAvailability:
    try:
        import transformers  # noqa: F401
        import huggingface_hub  # noqa: F401
    except (ModuleNotFoundError, OSError) as exc:
        return TransformersAvailability(
            available=False,
            reason=f"transformers reference runtime is not usable in this environment: {exc}",
        )
    return TransformersAvailability(available=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a Hugging Face reference model and write a config snapshot."
    )
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--artifact", default="artifacts/reference/qwen3_0_6b_reference_snapshot.json")
    parser.add_argument(
        "--config-only",
        action="store_true",
        help="Skip full weight loading and inspect only config/tokenizer metadata.",
    )
    parser.add_argument("--stdout", action="store_true")
    return parser


def _parameter_count(model: Any) -> tuple[int, int]:
    total = 0
    non_embedding = 0
    embedding_names = {
        "model.embed_tokens.weight",
        "lm_head.weight",
    }

    for name, param in model.named_parameters():
        count = param.numel()
        total += count
        if name not in embedding_names:
            non_embedding += count

    return total, non_embedding


def load_reference_snapshot(
    model_id: str = DEFAULT_MODEL_ID,
    *,
    config_only: bool = False,
) -> ReferenceSnapshot:
    import transformers
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

    config = AutoConfig.from_pretrained(model_id)
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = None
    parameter_count = None
    parameter_count_non_embedding = None
    model_class = None

    try:
        import torch

        torch_version = torch.__version__
    except Exception:
        torch_version = None

    if not config_only:
        model = AutoModelForCausalLM.from_pretrained(model_id, dtype="auto")
        parameter_count, parameter_count_non_embedding = _parameter_count(model)
        model_class = model.__class__.__name__

    return ReferenceSnapshot(
        model_id=model_id,
        architecture=(config.architectures[0] if getattr(config, "architectures", None) else None),
        model_type=getattr(config, "model_type", None),
        transformers_version=transformers.__version__,
        torch_version=torch_version,
        vocab_size=getattr(config, "vocab_size", None),
        hidden_size=getattr(config, "hidden_size", None),
        intermediate_size=getattr(config, "intermediate_size", None),
        num_hidden_layers=getattr(config, "num_hidden_layers", None),
        num_attention_heads=getattr(config, "num_attention_heads", None),
        num_key_value_heads=getattr(config, "num_key_value_heads", None),
        head_dim=getattr(config, "head_dim", None),
        hidden_act=getattr(config, "hidden_act", None),
        max_position_embeddings=getattr(config, "max_position_embeddings", None),
        max_window_layers=getattr(config, "max_window_layers", None),
        rms_norm_eps=getattr(config, "rms_norm_eps", None),
        rope_theta=getattr(config, "rope_theta", None),
        rope_scaling=getattr(config, "rope_scaling", None),
        attention_bias=getattr(config, "attention_bias", None),
        attention_dropout=getattr(config, "attention_dropout", None),
        use_cache=getattr(config, "use_cache", None),
        use_sliding_window=getattr(config, "use_sliding_window", None),
        sliding_window=getattr(config, "sliding_window", None),
        tie_word_embeddings=getattr(config, "tie_word_embeddings", None),
        bos_token_id=getattr(config, "bos_token_id", None),
        eos_token_id=getattr(config, "eos_token_id", None),
        torch_dtype=str(getattr(config, "torch_dtype", None)),
        parameter_count=parameter_count,
        parameter_count_non_embedding=parameter_count_non_embedding,
        tokenizer_class=tokenizer.__class__.__name__,
        config_class=config.__class__.__name__,
        model_class=model_class,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
    )


def write_reference_snapshot(snapshot: ReferenceSnapshot, artifact_path: str | Path) -> Path:
    path = Path(artifact_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(snapshot), indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    availability = check_transformers()
    if not availability.available:
        raise SystemExit(availability.reason)

    args = build_parser().parse_args()
    snapshot = load_reference_snapshot(args.model_id, config_only=args.config_only)
    artifact_path = write_reference_snapshot(snapshot, args.artifact)
    print(f"Wrote reference snapshot to {artifact_path}")
    if args.stdout:
        print(json.dumps(asdict(snapshot), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
