from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from qwen3_parity.weight_map import WeightMappingEntry, build_weight_mapping


@dataclass(frozen=True)
class WeightLoadResult:
    loaded_count: int
    missing_official_keys: tuple[str, ...]
    missing_scratch_keys: tuple[str, ...]


def _resolve_target(root: Any, dotted_path: str) -> Any:
    current = root
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        if part.isdigit():
            current = current[int(part)]
        else:
            current = getattr(current, part)
    return current, parts[-1]


def _copy_tensor_like(source: Any, target_param: Any) -> Any:
    if hasattr(source, "detach") and hasattr(source, "to"):
        copied = source.detach().to(dtype=target_param.dtype, device=target_param.device).clone()
    else:
        copied = target_param.new_tensor(source)
    return copied


def load_official_weights_into_scratch(
    model: Any,
    official_state_dict: dict[str, Any],
    *,
    mapping: Iterable[WeightMappingEntry] | None = None,
) -> WeightLoadResult:
    mapping_entries = list(mapping) if mapping is not None else build_weight_mapping(model.config)
    loaded_count = 0
    missing_official: list[str] = []
    missing_scratch: list[str] = []

    scratch_state = model.state_dict()

    for entry in mapping_entries:
        if entry.official_key not in official_state_dict:
            missing_official.append(entry.official_key)
            continue
        if entry.scratch_key not in scratch_state:
            missing_scratch.append(entry.scratch_key)
            continue

        source = official_state_dict[entry.official_key]
        target_tensor = scratch_state[entry.scratch_key]
        if tuple(getattr(source, "shape", ())) != tuple(target_tensor.shape):
            raise ValueError(
                f"Shape mismatch for {entry.official_key} -> {entry.scratch_key}: "
                f"official={getattr(source, 'shape', None)} scratch={tuple(target_tensor.shape)}"
            )

        target_parent, target_name = _resolve_target(model, entry.scratch_key)
        target_param = getattr(target_parent, target_name)
        copied = _copy_tensor_like(source, target_param)
        target_param.data.copy_(copied)
        loaded_count += 1

    return WeightLoadResult(
        loaded_count=loaded_count,
        missing_official_keys=tuple(missing_official),
        missing_scratch_keys=tuple(missing_scratch),
    )
