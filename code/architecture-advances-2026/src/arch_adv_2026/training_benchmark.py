from __future__ import annotations

import statistics
import time
from pathlib import Path
from typing import Any

from .config import ModelConfig, compression_falls_back_to_baseline, load_config
from .torch_model import build_tiny_torch_model, check_torch


def build_synthetic_autoregressive_batch(
    *,
    vocab_size: int,
    batch_size: int,
    seq_len: int,
    seed: int,
):
    availability = check_torch()
    if not availability.available:
        raise RuntimeError(availability.reason or "torch is not available")
    import torch

    if seq_len <= 0:
        raise ValueError("seq_len must be positive")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    torch.manual_seed(seed)
    starts = torch.randint(0, vocab_size, (batch_size, 1))
    strides = torch.randint(1, 4, (batch_size, 1))
    positions = torch.arange(seq_len + 1).unsqueeze(0)
    full_sequence = (starts + strides * positions) % vocab_size
    inputs = full_sequence[:, :-1].long()
    targets = full_sequence[:, 1:].long()
    return inputs, targets


def _global_grad_norm(parameters) -> float:
    availability = check_torch()
    if not availability.available:
        raise RuntimeError(availability.reason or "torch is not available")
    import torch

    grads = [param.grad.detach() for param in parameters if param.grad is not None]
    if not grads:
        return 0.0
    norms = [torch.sum(grad.float() * grad.float()) for grad in grads]
    total = torch.sum(torch.stack(norms))
    return float(torch.sqrt(total).item())


def run_torch_training_benchmark(
    config: ModelConfig,
    *,
    batch_size: int = 8,
    seq_len: int = 16,
    steps: int = 8,
    lr: float = 1e-2,
    seed: int = 0,
    clip_grad_norm: float | None = 1.0,
) -> dict[str, Any]:
    availability = check_torch()
    if not availability.available:
        raise RuntimeError(availability.reason or "torch is not available")
    import torch
    import torch.nn.functional as F

    if steps <= 0:
        raise ValueError("steps must be positive")
    if lr <= 0.0:
        raise ValueError("lr must be positive")

    torch.manual_seed(seed)
    model = build_tiny_torch_model(config, active_seq_len=seq_len)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

    step_rows: list[dict[str, Any]] = []
    nonfinite_step_count = 0

    for step_idx in range(steps):
        inputs, targets = build_synthetic_autoregressive_batch(
            vocab_size=config.vocab_size,
            batch_size=batch_size,
            seq_len=seq_len,
            seed=seed + step_idx,
        )
        optimizer.zero_grad(set_to_none=True)
        start = time.perf_counter()
        hidden, kv_cache, layer_means = model(inputs)
        logits = hidden @ model.embedding.weight.transpose(0, 1)
        loss = F.cross_entropy(logits.reshape(-1, config.vocab_size), targets.reshape(-1))
        loss.backward()
        grad_norm_before_clip = _global_grad_norm(model.parameters())
        if clip_grad_norm is not None:
            torch.nn.utils.clip_grad_norm_(model.parameters(), clip_grad_norm)
        grad_norm_after_clip = _global_grad_norm(model.parameters())
        optimizer.step()
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        loss_value = float(loss.detach().item())
        is_finite = bool(torch.isfinite(loss.detach()).item()) and grad_norm_after_clip == grad_norm_after_clip
        if not is_finite:
            nonfinite_step_count += 1
        step_rows.append(
            {
                "step": step_idx,
                "loss": loss_value,
                "grad_norm_before_clip": grad_norm_before_clip,
                "grad_norm_after_clip": grad_norm_after_clip,
                "elapsed_ms": elapsed_ms,
                "owner_cache_count": len(kv_cache),
                "last_layer_mean": layer_means[-1] if layer_means else None,
                "is_finite": is_finite,
            }
        )

    losses = [row["loss"] for row in step_rows]
    grad_norms = [row["grad_norm_before_clip"] for row in step_rows]
    elapsed = [row["elapsed_ms"] for row in step_rows]
    initial_loss = losses[0]
    final_loss = losses[-1]

    return {
        "name": config.name,
        "variant": config.variant.kind,
        "task": {
            "kind": "synthetic_autoregressive_progression",
            "batch_size": batch_size,
            "seq_len": seq_len,
            "steps": steps,
            "lr": lr,
            "seed": seed,
            "clip_grad_norm": clip_grad_norm,
        },
        "step_results": step_rows,
        "summary": {
            "initial_loss": initial_loss,
            "final_loss": final_loss,
            "min_loss": min(losses),
            "max_loss": max(losses),
            "loss_delta": final_loss - initial_loss,
            "loss_improvement_ratio": ((initial_loss - final_loss) / initial_loss) if initial_loss else 0.0,
            "max_grad_norm_before_clip": max(grad_norms),
            "mean_grad_norm_before_clip": statistics.fmean(grad_norms),
            "mean_step_ms": statistics.fmean(elapsed),
            "nonfinite_step_count": nonfinite_step_count,
            "all_steps_finite": nonfinite_step_count == 0,
            "owner_cache_count": step_rows[0]["owner_cache_count"],
        },
        "notes": [
            "This is a tiny Torch training-stability proxy on a synthetic next-token task.",
            "It is intended to compare whether architecture variants optimize cleanly under the same batch schedule.",
            "It does not replace real pretraining or finetuning experiments.",
        ],
    }


def compare_torch_training_benchmarks(
    baseline: ModelConfig,
    variant: ModelConfig,
    *,
    batch_size: int = 8,
    seq_len: int = 16,
    steps: int = 8,
    lr: float = 1e-2,
    seed: int = 0,
    clip_grad_norm: float | None = 1.0,
) -> dict[str, Any]:
    baseline_result = run_torch_training_benchmark(
        baseline,
        batch_size=batch_size,
        seq_len=seq_len,
        steps=steps,
        lr=lr,
        seed=seed,
        clip_grad_norm=clip_grad_norm,
    )
    if compression_falls_back_to_baseline(variant, seq_len):
        variant_result = {
            **baseline_result,
            "name": variant.name,
            "variant": variant.variant.kind,
        }
    else:
        variant_result = run_torch_training_benchmark(
            variant,
            batch_size=batch_size,
            seq_len=seq_len,
            steps=steps,
            lr=lr,
            seed=seed,
            clip_grad_norm=clip_grad_norm,
        )

    baseline_summary = baseline_result["summary"]
    variant_summary = variant_result["summary"]

    return {
        "baseline": baseline_result,
        "variant": variant_result,
        "comparison": {
            "final_loss_delta": variant_summary["final_loss"] - baseline_summary["final_loss"],
            "initial_loss_delta": variant_summary["initial_loss"] - baseline_summary["initial_loss"],
            "loss_improvement_ratio_delta": (
                variant_summary["loss_improvement_ratio"] - baseline_summary["loss_improvement_ratio"]
            ),
            "mean_step_ms_delta": variant_summary["mean_step_ms"] - baseline_summary["mean_step_ms"],
            "mean_step_ms_ratio_variant_over_baseline": (
                variant_summary["mean_step_ms"] / baseline_summary["mean_step_ms"]
                if baseline_summary["mean_step_ms"]
                else None
            ),
            "max_grad_norm_delta": (
                variant_summary["max_grad_norm_before_clip"] - baseline_summary["max_grad_norm_before_clip"]
            ),
            "owner_cache_delta": variant_summary["owner_cache_count"] - baseline_summary["owner_cache_count"],
            "both_all_steps_finite": (
                baseline_summary["all_steps_finite"] and variant_summary["all_steps_finite"]
            ),
        },
        "notes": [
            "Both runs use the same synthetic task family, learning rate, and batch schedule.",
            "Use this to catch optimization instability or unexpectedly slow training paths before heavier experiments.",
        ],
    }


def write_json_artifact(data: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(__import__("json").dumps(data, indent=2) + "\n", encoding="utf-8")
    return output_path


def load_config_pair(baseline_config: str | Path, variant_config: str | Path) -> tuple[ModelConfig, ModelConfig]:
    return load_config(baseline_config), load_config(variant_config)
