from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .hf_generate import generate_with_stack, load_generation_stack
from .hf_reference import DEFAULT_MODEL_ID, check_transformers


@dataclass(slots=True)
class PromptCase:
    name: str
    prompt: str
    prompt_mode: str = "chat"
    system_prompt: str | None = None
    enable_thinking: bool = False
    max_new_tokens: int = 48
    temperature: float = 0.0
    must_contain: list[str] | None = None
    must_not_contain: list[str] | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a small multi-prompt reference eval against a Hugging Face causal LM.")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--cases", required=True, help="Path to a JSONL prompt-case file.")
    parser.add_argument("--artifact", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def _load_cases(path: str | Path) -> list[PromptCase]:
    cases: list[PromptCase] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        cases.append(PromptCase(**payload))
    return cases


def _longest_common_prefix_chars(a: str, b: str) -> int:
    count = 0
    for left, right in zip(a, b):
        if left != right:
            break
        count += 1
    return count


def run_eval(cases: list[PromptCase], *, model_id: str = DEFAULT_MODEL_ID) -> dict[str, Any]:
    tokenizer, model = load_generation_stack(model_id)
    rows: list[dict[str, Any]] = []
    pass_count = 0

    for case in cases:
        artifact = generate_with_stack(
            tokenizer,
            model,
            case.prompt,
            model_id=model_id,
            prompt_mode=case.prompt_mode,
            system_prompt=case.system_prompt,
            enable_thinking=case.enable_thinking,
            max_new_tokens=case.max_new_tokens,
            temperature=case.temperature,
        )
        assistant_text = artifact.assistant_text.strip()
        must_contain = case.must_contain or []
        must_not_contain = case.must_not_contain or []
        contains_checks = {text: (text.lower() in assistant_text.lower()) for text in must_contain}
        forbidden_checks = {text: (text.lower() not in assistant_text.lower()) for text in must_not_contain}
        all_checks_pass = all(contains_checks.values()) and all(forbidden_checks.values())
        if all_checks_pass:
            pass_count += 1

        rows.append(
            {
                "case": case.name,
                "prompt_mode": case.prompt_mode,
                "input_token_count": artifact.input_token_count,
                "output_token_count": artifact.output_token_count,
                "assistant_char_count": len(assistant_text),
                "prompt_echo_prefix_chars": _longest_common_prefix_chars(case.prompt, assistant_text),
                "assistant_text": assistant_text,
                "checks": {
                    "must_contain": contains_checks,
                    "must_not_contain": forbidden_checks,
                },
                "passed": all_checks_pass,
            }
        )

    return {
        "model_id": model_id,
        "num_cases": len(cases),
        "num_passed": pass_count,
        "pass_rate": (pass_count / len(cases) if cases else 0.0),
        "case_results": rows,
        "notes": [
            "This is a lightweight prompt-behavior eval, not a quality benchmark.",
            "Use prompt echo, repeated failure patterns, and simple content checks to compare prompt formatting modes."
        ],
    }


def write_eval_artifact(result: dict[str, Any], artifact_path: str | Path) -> Path:
    path = Path(artifact_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    availability = check_transformers()
    if not availability.available:
        raise SystemExit(availability.reason)

    args = build_parser().parse_args()
    cases = _load_cases(args.cases)
    result = run_eval(cases, model_id=args.model_id)
    if args.artifact:
        path = write_eval_artifact(result, args.artifact)
        print(f"Wrote eval artifact to {path}")
    if args.stdout or not args.artifact:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
