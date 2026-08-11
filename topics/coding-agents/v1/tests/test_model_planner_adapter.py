from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from coding_agent_v1.model_planner_adapter import (
    ModelPlannerAdapterError,
    build_model_planner_prompt,
    extract_json_object,
    normalize_model_decision,
    run_model_planner_adapter,
)


def _planner_payload() -> dict[str, object]:
    return {
        "request": "fix the failing test",
        "workspace_root": "/repo",
        "instruction_files": ["README.md"],
        "deterministic_baseline": {
            "task_flow": "fix",
            "validation_command": "pytest -q",
            "reasons": ["deterministic selected fix"],
        },
        "contract": {
            "required_fields": ["task_flow", "reasons"],
            "allowed_task_flows": ["inspect", "fix", "feature", "rename", "diagnose", "resume"],
        },
    }


def test_build_model_planner_prompt_includes_contract_and_baseline() -> None:
    prompt = build_model_planner_prompt(_planner_payload())

    assert "Return only JSON" in prompt
    assert "Allowed task_flow values:" in prompt
    assert "fix the failing test" in prompt
    assert "deterministic selected fix" in prompt


def test_extract_json_object_accepts_fenced_json() -> None:
    parsed = extract_json_object(
        """```json
{"task_flow": "fix", "reasons": ["repair request"]}
```"""
    )

    assert parsed == {"task_flow": "fix", "reasons": ["repair request"]}


def test_extract_json_object_uses_last_json_object_when_cli_echoes_prompt() -> None:
    parsed = extract_json_object(
        """user
Required shape: {"task_flow": "<flow>", "reasons": ["reason"]}
assistant
{"task_flow": "diagnose", "reasons": ["final model decision"]}
"""
    )

    assert parsed == {"task_flow": "diagnose", "reasons": ["final model decision"]}


def test_extract_json_object_prefers_planner_decision_over_later_metadata() -> None:
    parsed = extract_json_object(
        """assistant
{"task_flow": "fix", "reasons": ["final model decision"]}
tokens
{"total": 123}
"""
    )

    assert parsed == {"task_flow": "fix", "reasons": ["final model decision"]}


def test_normalize_model_decision_rejects_unsupported_task_flow() -> None:
    with pytest.raises(ModelPlannerAdapterError, match="unsupported"):
        normalize_model_decision({"task_flow": "ship_it", "reasons": ["bad flow"]})


def test_normalize_model_decision_stringifies_feature_arguments() -> None:
    normalized = normalize_model_decision(
        {
            "task_flow": "feature",
            "reasons": "add CLI option",
            "feature_strategy": "cli_flag",
            "feature_arguments": {"flag_name": "--verbose", "enabled": True},
        }
    )

    assert normalized == {
        "task_flow": "feature",
        "reasons": ["add CLI option"],
        "feature_strategy": "cli_flag",
        "feature_arguments": {"flag_name": "--verbose", "enabled": "True"},
    }


def test_run_model_planner_adapter_uses_external_model_command(tmp_path: Path) -> None:
    model_script = tmp_path / "model.py"
    model_script.write_text(
        "import json, sys\n"
        "prompt = sys.stdin.read()\n"
        "assert 'deterministic selected fix' in prompt\n"
        "print('```json')\n"
        "print(json.dumps({'task_flow': 'fix', 'reasons': ['model kept repair flow']}))\n"
        "print('```')\n",
        encoding="utf-8",
    )

    decision = run_model_planner_adapter(
        _planner_payload(),
        f"{sys.executable} {model_script}",
    )

    assert decision == {"task_flow": "fix", "reasons": ["model kept repair flow"]}


def test_run_model_planner_adapter_rejects_invalid_model_json(tmp_path: Path) -> None:
    model_script = tmp_path / "model.py"
    model_script.write_text("print('not json')\n", encoding="utf-8")

    with pytest.raises(ModelPlannerAdapterError, match="JSON must be an object"):
        run_model_planner_adapter(
            _planner_payload(),
            f"{sys.executable} {model_script}",
        )
