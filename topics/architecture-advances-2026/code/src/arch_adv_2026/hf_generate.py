from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .hf_reference import DEFAULT_MODEL_ID, check_transformers


@dataclass(slots=True)
class GenerationArtifact:
    model_id: str
    prompt: str
    prompt_mode: str
    system_prompt: str | None
    enable_thinking: bool
    max_new_tokens: int
    temperature: float
    do_sample: bool
    input_token_count: int
    output_token_count: int
    rendered_prompt_text: str
    generated_text: str
    assistant_text: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a small reference generation against a Hugging Face causal LM."
    )
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--prompt-mode", choices=["plain", "chat"], default="chat")
    parser.add_argument("--system-prompt", default=None)
    parser.add_argument("--enable-thinking", action="store_true")
    parser.add_argument("--artifact", default=None)
    parser.add_argument("--max-new-tokens", type=int, default=32)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--stdout", action="store_true")
    return parser


def load_generation_stack(model_id: str = DEFAULT_MODEL_ID) -> tuple[Any, Any]:
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, dtype="auto")
    model.eval()
    return tokenizer, model


def build_messages(prompt: str, system_prompt: str | None = None) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    return messages


def prepare_inputs(
    tokenizer: Any,
    prompt: str,
    *,
    prompt_mode: str,
    system_prompt: str | None,
    enable_thinking: bool,
) -> tuple[dict[str, Any], str]:
    if prompt_mode == "chat":
        messages = build_messages(prompt, system_prompt)
        if hasattr(tokenizer, "apply_chat_template"):
            encoded = tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                enable_thinking=enable_thinking,
                return_tensors="pt",
                return_dict=True,
            )
            rendered_prompt_text = tokenizer.decode(encoded["input_ids"][0], skip_special_tokens=False)
            return encoded, rendered_prompt_text
    encoded = tokenizer(prompt, return_tensors="pt")
    return encoded, prompt


def generate_with_stack(
    tokenizer: Any,
    model: Any,
    prompt: str,
    *,
    model_id: str = DEFAULT_MODEL_ID,
    prompt_mode: str = "chat",
    system_prompt: str | None = None,
    enable_thinking: bool = False,
    max_new_tokens: int = 32,
    temperature: float = 0.0,
) -> GenerationArtifact:
    import torch

    encoded, rendered_prompt_text = prepare_inputs(
        tokenizer,
        prompt,
        prompt_mode=prompt_mode,
        system_prompt=system_prompt,
        enable_thinking=enable_thinking,
    )
    do_sample = temperature > 0.0
    generation_kwargs = {
        **encoded,
        "max_new_tokens": max_new_tokens,
        "do_sample": do_sample,
        "pad_token_id": tokenizer.eos_token_id,
    }
    if do_sample:
        generation_kwargs["temperature"] = temperature
    with torch.no_grad():
        generated = model.generate(**generation_kwargs)

    input_token_count = int(encoded["input_ids"].shape[-1])
    output_token_count = int(generated.shape[-1])
    assistant_ids = generated[0, input_token_count:]
    assistant_text = tokenizer.decode(assistant_ids, skip_special_tokens=True)
    generated_text = tokenizer.decode(generated[0], skip_special_tokens=True)
    return GenerationArtifact(
        model_id=model_id,
        prompt=prompt,
        prompt_mode=prompt_mode,
        system_prompt=system_prompt,
        enable_thinking=enable_thinking,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        do_sample=do_sample,
        input_token_count=input_token_count,
        output_token_count=output_token_count,
        rendered_prompt_text=rendered_prompt_text,
        generated_text=generated_text,
        assistant_text=assistant_text,
    )


def generate_completion(
    prompt: str,
    *,
    model_id: str = DEFAULT_MODEL_ID,
    prompt_mode: str = "chat",
    system_prompt: str | None = None,
    enable_thinking: bool = False,
    max_new_tokens: int = 32,
    temperature: float = 0.0,
) -> GenerationArtifact:
    tokenizer, model = load_generation_stack(model_id)
    return generate_with_stack(
        tokenizer,
        model,
        prompt,
        model_id=model_id,
        prompt_mode=prompt_mode,
        system_prompt=system_prompt,
        enable_thinking=enable_thinking,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
    )


def write_generation_artifact(artifact: GenerationArtifact, artifact_path: str | Path) -> Path:
    path = Path(artifact_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(artifact), indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    availability = check_transformers()
    if not availability.available:
        raise SystemExit(availability.reason)

    args = build_parser().parse_args()
    artifact = generate_completion(
        args.prompt,
        model_id=args.model_id,
        prompt_mode=args.prompt_mode,
        system_prompt=args.system_prompt,
        enable_thinking=args.enable_thinking,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
    )
    if args.artifact:
        path = write_generation_artifact(artifact, args.artifact)
        print(f"Wrote generation artifact to {path}")
    if args.stdout or not args.artifact:
        print(json.dumps(asdict(artifact), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
