import json
from pathlib import Path

import pytest

from coding_agent_v1.trace_schema import default_trace_schema_path, load_trace_schema, validate_trace_payload


def test_default_trace_schema_path_points_to_shared_schema() -> None:
    path = default_trace_schema_path()

    assert path.name == "trace-schema-v1.json"
    assert path.exists()


def test_load_trace_schema_reads_shared_schema() -> None:
    schema = load_trace_schema()

    assert schema["title"] == "Agent Eval Trace V1"
    assert "properties" in schema
    assert "steps" in schema["properties"]


def test_validate_trace_payload_accepts_sample_success_trace() -> None:
    path = (
        Path(__file__).resolve().parents[3]
        / "agent-evals" / "evals" / "datasets"
        / "sample-success-trace.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))

    validate_trace_payload(payload)


def test_validate_trace_payload_rejects_bad_enum_value() -> None:
    path = (
        Path(__file__).resolve().parents[3]
        / "agent-evals" / "evals" / "datasets"
        / "sample-success-trace.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["task_class"] = "bad-class"

    with pytest.raises(ValueError, match="must be one of"):
        validate_trace_payload(payload)
