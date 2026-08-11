from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .hf_generate import generate_with_stack, load_generation_stack
from .hf_reference import DEFAULT_MODEL_ID, check_transformers


@dataclass(slots=True)
class LongContextCase:
    name: str
    task_type: str
    prompt: str
    answer: str
    answer_match: str = "exact"
    prompt_mode: str = "chat"
    system_prompt: str | None = None
    enable_thinking: bool = False
    max_new_tokens: int = 24
    temperature: float = 0.0
    metadata: dict[str, Any] | None = None


def build_generator_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic long-context cases.")
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--num-cases", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--filler-repeats", type=int, default=48)
    parser.add_argument("--stdout", action="store_true")
    return parser


def build_eval_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run synthetic long-context eval cases against a Hugging Face model.")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--artifact", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def build_sweep_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a synthetic long-context sweep across multiple filler lengths."
    )
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--filler-repeats", default="8,16,32")
    parser.add_argument("--cases-per-length", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sweep-runs", type=int, default=1)
    parser.add_argument("--artifact", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def _dtype_nbytes(dtype: Any) -> int:
    name = str(dtype)
    if "bfloat16" in name or "float16" in name:
        return 2
    if "float32" in name:
        return 4
    if "float64" in name:
        return 8
    return 2


def _estimate_kv_cache_bytes(
    *,
    seq_len: int,
    num_hidden_layers: int,
    num_key_value_heads: int,
    head_dim: int,
    bytes_per_element: int,
    batch_size: int = 1,
) -> int:
    return (
        batch_size
        * num_hidden_layers
        * 2
        * num_key_value_heads
        * seq_len
        * head_dim
        * bytes_per_element
    )


def score_answer(prediction: str, expected: str, *, match: str = "exact") -> bool:
    if match == "substring":
        return _normalize_text(expected) in _normalize_text(prediction)
    if match == "exact":
        return _normalize_text(prediction) == _normalize_text(expected)
    raise ValueError(f"unsupported answer match mode: {match}")


def _filler_paragraph(index: int) -> str:
    return (
        f"Document section {index}: long-context evaluation needs repeated background text about "
        f"memory, retrieval, and attention so that the answer signal is surrounded by irrelevant detail."
    )


def build_passkey_case(index: int, *, rng: random.Random, filler_repeats: int) -> LongContextCase:
    passkey = f"{rng.randint(10000, 99999)}"
    insertion_point = rng.randint(8, max(8, filler_repeats - 8))
    sections = []
    for section_idx in range(filler_repeats):
        sections.append(_filler_paragraph(section_idx))
        if section_idx == insertion_point:
            sections.append(f"Important record: the passkey for session {index} is {passkey}. Memorize it exactly.")
    context = "\n".join(sections)
    prompt = (
        "Read the following long document and answer with only the passkey digits.\n\n"
        f"{context}\n\n"
        "Question: What is the passkey?"
    )
    return LongContextCase(
        name=f"passkey_{index}",
        task_type="passkey_retrieval",
        prompt=prompt,
        answer=passkey,
        answer_match="substring",
        system_prompt=(
            "You are a precise retrieval assistant. Answer in English with only the requested final answer. "
            "Do not output reasoning traces or <think> tags."
        ),
        metadata={
            "filler_repeats": filler_repeats,
            "insertion_section": insertion_point,
            "answer_length": len(passkey),
        },
    )


def build_needle_case(index: int, *, rng: random.Random, filler_repeats: int) -> LongContextCase:
    city = rng.choice(["Lima", "Oslo", "Seoul", "Nairobi", "Lisbon", "Kyoto"])
    color = rng.choice(["amber", "teal", "scarlet", "silver", "gold", "violet"])
    insertion_point = rng.randint(8, max(8, filler_repeats - 8))
    sections = []
    for section_idx in range(filler_repeats):
        sections.append(_filler_paragraph(section_idx))
        if section_idx == insertion_point:
            sections.append(
                f"Needle fact: the special marker for archive {index} is the {color} lantern in {city}."
            )
    context = "\n".join(sections)
    prompt = (
        "Read the following long document and answer with the exact marker phrase only.\n\n"
        f"{context}\n\n"
        "Question: What is the special marker?"
    )
    answer = f"{color} lantern in {city}"
    return LongContextCase(
        name=f"needle_{index}",
        task_type="needle_retrieval",
        prompt=prompt,
        answer=answer,
        answer_match="substring",
        system_prompt=(
            "You are a precise retrieval assistant. Answer in English with only the requested final answer. "
            "Do not output reasoning traces or <think> tags."
        ),
        metadata={
            "filler_repeats": filler_repeats,
            "insertion_section": insertion_point,
            "city": city,
            "color": color,
        },
    )


def build_synthetic_cases(*, num_cases: int = 4, seed: int = 0, filler_repeats: int = 48) -> list[LongContextCase]:
    rng = random.Random(seed)
    cases: list[LongContextCase] = []
    for index in range(num_cases):
        if index % 2 == 0:
            cases.append(build_passkey_case(index, rng=rng, filler_repeats=filler_repeats))
        else:
            cases.append(build_needle_case(index, rng=rng, filler_repeats=filler_repeats))
    return cases


def build_sweep_cases(
    *,
    filler_repeat_values: list[int],
    cases_per_length: int = 2,
    seed: int = 0,
) -> list[LongContextCase]:
    cases: list[LongContextCase] = []
    for bucket_idx, filler_repeats in enumerate(filler_repeat_values):
        bucket_cases = build_synthetic_cases(
            num_cases=cases_per_length,
            seed=seed + bucket_idx,
            filler_repeats=filler_repeats,
        )
        for case_idx, case in enumerate(bucket_cases):
            case.name = f"{case.name}_len{filler_repeats}_idx{case_idx}"
        cases.extend(bucket_cases)
    return cases


def write_cases(cases: list[LongContextCase], artifact_path: str | Path) -> Path:
    path = Path(artifact_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(asdict(case)) + "\n")
    return path


def load_cases(path: str | Path) -> list[LongContextCase]:
    cases: list[LongContextCase] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        cases.append(LongContextCase(**json.loads(stripped)))
    return cases


def run_long_context_eval(cases: list[LongContextCase], *, model_id: str = DEFAULT_MODEL_ID) -> dict[str, Any]:
    tokenizer, model = load_generation_stack(model_id)
    config = model.config
    bytes_per_element = _dtype_nbytes(model.dtype)
    rows: list[dict[str, Any]] = []
    pass_count = 0

    for case in cases:
        started_at = time.perf_counter()
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
        elapsed_ms = (time.perf_counter() - started_at) * 1000.0
        assistant_text = artifact.assistant_text.strip()
        passed = score_answer(assistant_text, case.answer, match=case.answer_match)
        if passed:
            pass_count += 1
        generated_token_count = max(0, artifact.output_token_count - artifact.input_token_count)
        elapsed_seconds = max(elapsed_ms / 1000.0, 1e-9)
        estimated_kv_cache_bytes = _estimate_kv_cache_bytes(
            seq_len=artifact.input_token_count,
            num_hidden_layers=int(getattr(config, "num_hidden_layers", 0)),
            num_key_value_heads=int(getattr(config, "num_key_value_heads", 0)),
            head_dim=int(getattr(config, "head_dim", 0)),
            bytes_per_element=bytes_per_element,
        )
        rows.append(
            {
                "case": case.name,
                "task_type": case.task_type,
                "expected_answer": case.answer,
                "assistant_text": assistant_text,
                "passed": passed,
                "answer_match": case.answer_match,
                "input_token_count": artifact.input_token_count,
                "output_token_count": artifact.output_token_count,
                "generated_token_count": generated_token_count,
                "prompt_char_count": len(case.prompt),
                "elapsed_ms": elapsed_ms,
                "generated_tokens_per_second": generated_token_count / elapsed_seconds,
                "total_tokens_per_second": artifact.output_token_count / elapsed_seconds,
                "estimated_kv_cache_bytes": estimated_kv_cache_bytes,
                "metadata": case.metadata or {},
            }
        )

    return {
        "model_id": model_id,
        "num_cases": len(cases),
        "num_passed": pass_count,
        "pass_rate": (pass_count / len(cases) if cases else 0.0),
        "case_results": rows,
        "notes": [
            "This is a synthetic long-context retrieval eval built to stress context use, not world knowledge.",
            "Use it as an early signal for retrieval behavior before heavier benchmark work."
        ],
    }


def _group_rows_by_filler_repeats(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        filler_repeats = int(row.get("metadata", {}).get("filler_repeats", -1))
        grouped.setdefault(filler_repeats, []).append(row)

    summaries: list[dict[str, Any]] = []
    for filler_repeats in sorted(grouped):
        bucket_rows = grouped[filler_repeats]
        elapsed_values = [row["elapsed_ms"] for row in bucket_rows]
        input_tokens = [row["input_token_count"] for row in bucket_rows]
        output_tokens = [row["output_token_count"] for row in bucket_rows]
        generated_tokens = [row["generated_token_count"] for row in bucket_rows]
        generated_tps = [row["generated_tokens_per_second"] for row in bucket_rows]
        total_tps = [row["total_tokens_per_second"] for row in bucket_rows]
        kv_cache_bytes = [row["estimated_kv_cache_bytes"] for row in bucket_rows]
        pass_count = sum(1 for row in bucket_rows if row["passed"])
        summaries.append(
            {
                "filler_repeats": filler_repeats,
                "num_cases": len(bucket_rows),
                "num_passed": pass_count,
                "pass_rate": (pass_count / len(bucket_rows) if bucket_rows else 0.0),
                "mean_elapsed_ms": statistics.fmean(elapsed_values),
                "min_elapsed_ms": min(elapsed_values),
                "max_elapsed_ms": max(elapsed_values),
                "mean_input_token_count": statistics.fmean(input_tokens),
                "mean_output_token_count": statistics.fmean(output_tokens),
                "mean_generated_token_count": statistics.fmean(generated_tokens),
                "mean_generated_tokens_per_second": statistics.fmean(generated_tps),
                "mean_total_tokens_per_second": statistics.fmean(total_tps),
                "mean_estimated_kv_cache_bytes": statistics.fmean(kv_cache_bytes),
            }
        )
    return summaries


def _group_bucket_summaries(bucket_runs: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for bucket_rows in bucket_runs:
        for row in bucket_rows:
            grouped.setdefault(int(row["filler_repeats"]), []).append(row)

    summaries: list[dict[str, Any]] = []
    for filler_repeats in sorted(grouped):
        rows = grouped[filler_repeats]
        pass_rates = [row["pass_rate"] for row in rows]
        elapsed = [row["mean_elapsed_ms"] for row in rows]
        gen_tps = [row["mean_generated_tokens_per_second"] for row in rows]
        total_tps = [row["mean_total_tokens_per_second"] for row in rows]
        kv_bytes = [row["mean_estimated_kv_cache_bytes"] for row in rows]
        summaries.append(
            {
                "filler_repeats": filler_repeats,
                "num_runs": len(rows),
                "mean_pass_rate": statistics.fmean(pass_rates),
                "min_pass_rate": min(pass_rates),
                "max_pass_rate": max(pass_rates),
                "pass_rate_stdev": statistics.pstdev(pass_rates) if len(pass_rates) > 1 else 0.0,
                "mean_elapsed_ms": statistics.fmean(elapsed),
                "min_elapsed_ms": min(elapsed),
                "max_elapsed_ms": max(elapsed),
                "elapsed_ms_stdev": statistics.pstdev(elapsed) if len(elapsed) > 1 else 0.0,
                "mean_generated_tokens_per_second": statistics.fmean(gen_tps),
                "mean_total_tokens_per_second": statistics.fmean(total_tps),
                "mean_estimated_kv_cache_bytes": statistics.fmean(kv_bytes),
                "num_cases_per_run": rows[0]["num_cases"],
            }
        )
    return summaries


def run_long_context_sweep(
    *,
    model_id: str = DEFAULT_MODEL_ID,
    filler_repeat_values: list[int],
    cases_per_length: int = 2,
    seed: int = 0,
    sweep_runs: int = 1,
) -> dict[str, Any]:
    if sweep_runs <= 0:
        raise ValueError("sweep_runs must be positive")

    run_results: list[dict[str, Any]] = []
    bucket_runs: list[list[dict[str, Any]]] = []
    all_case_results: list[dict[str, Any]] = []
    total_cases = 0
    total_passed = 0

    for run_idx in range(sweep_runs):
        run_seed = seed + run_idx
        cases = build_sweep_cases(
            filler_repeat_values=filler_repeat_values,
            cases_per_length=cases_per_length,
            seed=run_seed,
        )
        result = run_long_context_eval(cases, model_id=model_id)
        for row in result["case_results"]:
            row["run_index"] = run_idx
            row["run_seed"] = run_seed
        all_case_results.extend(result["case_results"])
        total_cases += result["num_cases"]
        total_passed += result["num_passed"]
        buckets = _group_rows_by_filler_repeats(result["case_results"])
        bucket_runs.append(buckets)
        run_results.append(
            {
                "run_index": run_idx,
                "seed": run_seed,
                "num_cases": result["num_cases"],
                "num_passed": result["num_passed"],
                "pass_rate": result["pass_rate"],
                "length_buckets": buckets,
            }
        )

    return {
        "model_id": model_id,
        "num_cases": total_cases,
        "num_passed": total_passed,
        "pass_rate": (total_passed / total_cases if total_cases else 0.0),
        "case_results": all_case_results,
        "sweep": {
            "filler_repeat_values": filler_repeat_values,
            "cases_per_length": cases_per_length,
            "seed": seed,
            "sweep_runs": sweep_runs,
            "run_results": run_results,
            "length_buckets": _group_bucket_summaries(bucket_runs),
        },
        "notes": [
            "This sweep varies synthetic context length via filler repeats and records both retrieval accuracy and latency.",
            "Use it to see how quality and runtime change together as prompt length grows.",
            "Multiple sweep runs aggregate independent synthetic case draws so each length bucket is less anecdotal."
        ],
    }


def write_eval_artifact(result: dict[str, Any], artifact_path: str | Path) -> Path:
    path = Path(artifact_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return path


def main_generate() -> int:
    args = build_generator_parser().parse_args()
    cases = build_synthetic_cases(
        num_cases=args.num_cases,
        seed=args.seed,
        filler_repeats=args.filler_repeats,
    )
    path = write_cases(cases, args.artifact)
    print(f"Wrote synthetic long-context cases to {path}")
    if args.stdout:
        for case in cases:
            print(json.dumps(asdict(case), indent=2))
    return 0


def main_eval() -> int:
    availability = check_transformers()
    if not availability.available:
        raise SystemExit(availability.reason)

    args = build_eval_parser().parse_args()
    result = run_long_context_eval(load_cases(args.cases), model_id=args.model_id)
    if args.artifact:
        path = write_eval_artifact(result, args.artifact)
        print(f"Wrote long-context eval artifact to {path}")
    if args.stdout or not args.artifact:
        print(json.dumps(result, indent=2))
    return 0


def main_sweep() -> int:
    availability = check_transformers()
    if not availability.available:
        raise SystemExit(availability.reason)

    args = build_sweep_parser().parse_args()
    filler_repeat_values = [int(value.strip()) for value in args.filler_repeats.split(",") if value.strip()]
    if not filler_repeat_values:
        raise SystemExit("at least one filler repeat value is required")
    result = run_long_context_sweep(
        model_id=args.model_id,
        filler_repeat_values=filler_repeat_values,
        cases_per_length=args.cases_per_length,
        seed=args.seed,
        sweep_runs=args.sweep_runs,
    )
    if args.artifact:
        path = write_eval_artifact(result, args.artifact)
        print(f"Wrote long-context sweep artifact to {path}")
    if args.stdout or not args.artifact:
        print(json.dumps(result, indent=2))
    return 0
