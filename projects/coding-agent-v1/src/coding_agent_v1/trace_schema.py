from __future__ import annotations

import json
from pathlib import Path


def default_trace_schema_path() -> Path:
    return (
        Path(__file__).resolve().parents[4]
        / "evals"
        / "agent-evals"
        / "datasets"
        / "trace-schema-v1.json"
    )


def load_trace_schema(path: Path | None = None) -> dict[str, object]:
    schema_path = path or default_trace_schema_path()
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_trace_payload(
    payload: object,
    *,
    schema: dict[str, object] | None = None,
    schema_path: Path | None = None,
) -> None:
    active_schema = schema if schema is not None else load_trace_schema(schema_path)
    _validate_node(payload, active_schema, "$")


def _validate_node(value: object, schema: dict[str, object], path: str) -> None:
    expected_type = schema.get("type")
    if expected_type is not None:
        _validate_type(value, expected_type, path)

    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        raise ValueError(f"{path} must be one of {enum_values!r}, got {value!r}")

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            raise ValueError(f"{path} must have minLength={min_length}, got {len(value)}")

    if isinstance(value, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            raise ValueError(f"{path} must have minItems={min_items}, got {len(value)}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_node(item, item_schema, f"{path}[{index}]")

    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    raise ValueError(f"{path} is missing required property {key!r}")

        properties = schema.get("properties", {})
        additional_properties = schema.get("additionalProperties", True)
        if isinstance(properties, dict):
            for key, item in value.items():
                if key in properties:
                    item_schema = properties[key]
                    if isinstance(item_schema, dict):
                        _validate_node(item, item_schema, f"{path}.{key}")
                    continue
                if additional_properties is False:
                    raise ValueError(f"{path} has unexpected property {key!r}")
                if isinstance(additional_properties, dict):
                    _validate_node(item, additional_properties, f"{path}.{key}")


def _validate_type(value: object, expected_type: object, path: str) -> None:
    if isinstance(expected_type, list):
        if any(_matches_type(value, item) for item in expected_type):
            return
        raise ValueError(f"{path} must have one of types {expected_type!r}, got {type(value).__name__}")
    if isinstance(expected_type, str):
        if _matches_type(value, expected_type):
            return
        raise ValueError(f"{path} must have type {expected_type!r}, got {type(value).__name__}")


def _matches_type(value: object, expected_type: object) -> bool:
    mapping = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: (isinstance(item, int) or isinstance(item, float)) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "null": lambda item: item is None,
    }
    checker = mapping.get(expected_type)
    if checker is None:
        return False
    return checker(value)
