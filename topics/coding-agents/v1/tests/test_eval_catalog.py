from pathlib import Path

import pytest

from coding_agent_v1.eval_catalog import (
    build_eval_scenario_pack_summary,
    list_executable_eval_scenarios,
    load_eval_scenario_pack,
    summarize_eval_scenario_pack,
)


def test_load_eval_scenario_pack_parses_core_catalog() -> None:
    path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "core-v1.json"

    pack = load_eval_scenario_pack(path)

    assert pack.pack_id == "coding-agent-v1-core"
    assert len(pack.scenarios) == 20
    assert {scenario.task_class for scenario in pack.scenarios} == {
        "fix",
        "feature",
        "rename",
        "diagnose",
        "resume",
    }
    assert all(scenario.failure_modes for scenario in pack.scenarios)
    assert all(scenario.available_tools for scenario in pack.scenarios)
    assert all(scenario.expected_tool_sequence for scenario in pack.scenarios)


def test_load_eval_scenario_pack_parses_smoke_catalog() -> None:
    path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "smoke-v1.json"

    pack = load_eval_scenario_pack(path)

    assert pack.pack_id == "coding-agent-v1-smoke"
    assert len(pack.scenarios) == 5
    assert {scenario.task_class for scenario in pack.scenarios} == {
        "fix",
        "feature",
        "rename",
        "diagnose",
        "resume",
    }
    assert {scenario.severity for scenario in pack.scenarios} == {"smoke"}
    assert all(scenario.failure_modes for scenario in pack.scenarios)
    assert pack.scenarios[0].planner_strategy == "deterministic_heuristic"
    assert all(scenario.planner_strategy for scenario in pack.scenarios)


def test_load_eval_scenario_pack_parses_stress_catalog() -> None:
    path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "stress-v1.json"

    pack = load_eval_scenario_pack(path)

    assert pack.pack_id == "coding-agent-v1-stress"
    assert len(pack.scenarios) == 5
    assert {scenario.task_class for scenario in pack.scenarios} == {
        "fix",
        "feature",
        "rename",
        "diagnose",
        "resume",
    }
    assert {scenario.severity for scenario in pack.scenarios} == {"core"}
    assert all(scenario.failure_modes for scenario in pack.scenarios)
    assert all(scenario.available_tools for scenario in pack.scenarios)
    assert all(scenario.expected_tool_sequence for scenario in pack.scenarios)


def test_load_eval_scenario_pack_parses_richer_fields_in_stress_catalog() -> None:
    path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "stress-v1.json"

    pack = load_eval_scenario_pack(path)

    by_id = {scenario.scenario_id: scenario for scenario in pack.scenarios}
    diagnose = by_id["diagnose-003"]
    rename = by_id["rename-004"]
    resume = by_id["resume-003"]

    assert diagnose.expected_escalation_behavior == "ask_before_write"
    assert diagnose.first_failure_state_if_broken == ("request_approval", "execute_tool", "finish")
    assert diagnose.available_tools[-1]["name"] == "edit_file"
    assert any("approval boundary" in item for item in diagnose.trace_requirements)

    assert rename.expected_tool_sequence == ("search_code", "read_file", "edit_file", "run_command")
    assert rename.first_failure_state_if_broken == ("generate_tool_arguments", "execute_tool", "validate")
    assert any("global replacement" in item for item in rename.trace_requirements)

    assert resume.available_tools[0]["name"] == "read_memory"
    assert resume.expected_escalation_behavior == "not_needed"
    assert any("resumed diagnose-only context" in item for item in resume.trace_requirements)


def test_load_eval_scenario_pack_parses_planner_superiority_catalog() -> None:
    path = (
        Path(__file__).resolve().parents[3]
        / "coding-agents" / "evals" / "scenarios"
        / "planner-quality-v2.json"
    )

    pack = load_eval_scenario_pack(path)

    assert pack.pack_id == "coding-agent-v1-planner-quality-v2"
    assert len(pack.scenarios) == 10
    assert {scenario.severity for scenario in pack.scenarios} == {"stretch"}
    assert {scenario.task_class for scenario in pack.scenarios} == {
        "fix",
        "feature",
        "rename",
        "diagnose",
        "resume",
    }
    assert all("planner-superiority" in scenario.tags for scenario in pack.scenarios)
    assert all(scenario.expected_tool_sequence for scenario in pack.scenarios)


def test_list_executable_eval_scenarios_filters_to_runnable_subset() -> None:
    path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "core-v1.json"

    pack = load_eval_scenario_pack(path)
    executable = list_executable_eval_scenarios(pack)

    assert len(executable) == 20
    assert {scenario.setup_kind for scenario in executable} == {
        "repair",
        "repair_nested_literal",
        "repair_literal_regression_guard",
        "rename",
        "rename_fixture_refs",
        "rename_nested_package",
        "rename_ambiguous_mentions",
        "cli_flag",
        "config_option",
        "env_var",
        "diagnose",
        "diagnose_multi_test",
        "approval_boundary",
        "diagnose_repo_fallback",
        "resume_flow",
        "resume_repair_flow",
        "resume_diagnose_flow",
        "resume_validation_reminder",
    }


def test_build_eval_scenario_pack_summary_counts_task_classes_and_failure_modes() -> None:
    path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "core-v1.json"
    pack = load_eval_scenario_pack(path)

    summary = build_eval_scenario_pack_summary(pack)

    assert summary.scenario_count == 20
    assert summary.task_class_counts == {
        "diagnose": 4,
        "feature": 4,
        "fix": 4,
        "rename": 4,
        "resume": 4,
    }
    assert summary.severity_counts == {
        "core": 15,
        "smoke": 5,
    }
    assert summary.failure_mode_counts["wrong_file_touched"] >= 1
    assert summary.failure_mode_counts["bad_validation_scope"] >= 1


def test_load_eval_scenario_pack_parses_richer_fields_in_core_catalog() -> None:
    path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "core-v1.json"

    pack = load_eval_scenario_pack(path)
    by_id = {scenario.scenario_id: scenario for scenario in pack.scenarios}

    fix = by_id["fix-003"]
    diagnose = by_id["diagnose-003"]
    resume = by_id["resume-002"]

    assert fix.expected_tool_sequence == ("run_command", "read_file", "edit_file", "run_command")
    assert fix.first_failure_state_if_broken == ("generate_tool_arguments", "execute_tool", "validate")
    assert any("nested test path" in item for item in fix.trace_requirements)

    assert diagnose.expected_escalation_behavior == "ask_before_write"
    assert diagnose.available_tools[-1]["name"] == "edit_file"
    assert diagnose.first_failure_state_if_broken == ("request_approval", "execute_tool", "finish")

    assert resume.available_tools[0]["name"] == "read_memory"
    assert resume.expected_tool_sequence == ("read_memory", "run_command")
    assert any("prior repair context" in item for item in resume.trace_requirements)


def test_summarize_eval_scenario_pack_lists_counts() -> None:
    path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "core-v1.json"
    pack = load_eval_scenario_pack(path)

    text = summarize_eval_scenario_pack(pack)

    assert "pack_id: coding-agent-v1-core" in text
    assert "scenario_count: 20" in text
    assert "task_classes:" in text
    assert "  fix: 4" in text
    assert "failure_modes:" in text


def test_build_eval_scenario_pack_summary_counts_smoke_catalog() -> None:
    path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "smoke-v1.json"
    pack = load_eval_scenario_pack(path)

    summary = build_eval_scenario_pack_summary(pack)

    assert summary.scenario_count == 5
    assert summary.task_class_counts == {
        "diagnose": 1,
        "feature": 1,
        "fix": 1,
        "rename": 1,
        "resume": 1,
    }
    assert summary.severity_counts == {"smoke": 5}


def test_build_eval_scenario_pack_summary_counts_stress_catalog() -> None:
    path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "stress-v1.json"
    pack = load_eval_scenario_pack(path)

    summary = build_eval_scenario_pack_summary(pack)

    assert summary.scenario_count == 5
    assert summary.task_class_counts == {
        "diagnose": 1,
        "feature": 1,
        "fix": 1,
        "rename": 1,
        "resume": 1,
    }
    assert summary.severity_counts == {"core": 5}
    assert summary.failure_mode_counts["unsafe_action"] >= 2


def test_load_eval_scenario_pack_rejects_invalid_task_class(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(
        """
{
  "pack_id": "invalid",
  "title": "Invalid",
  "description": "bad task class",
  "scenarios": [
    {
      "scenario_id": "invalid-1",
      "title": "Invalid task class",
      "task_class": "plan",
      "severity": "core",
      "request": "do something",
      "expected_outcome": "something",
      "failure_modes": ["no_op"],
      "tags": ["invalid"]
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported task_class: plan"):
        load_eval_scenario_pack(path)


def test_load_eval_scenario_pack_parses_richer_agent_eval_fields() -> None:
    path = (
        Path(__file__).resolve().parents[3]
        / "agent-evals" / "evals" / "scenarios"
        / "coding-agent-v1-smoke-v1.json"
    )

    pack = load_eval_scenario_pack(path)

    assert pack.pack_id == "coding-agent-v1-agent-evals-smoke"
    assert len(pack.scenarios) == 5
    first = pack.scenarios[0]
    assert first.available_tools
    assert first.available_tools[0]["name"] == "read_file"
    assert first.expected_tool_sequence == ("run_command", "read_file", "edit_file", "run_command")
    assert first.expected_escalation_behavior == "not_needed"
    assert first.first_failure_state_if_broken == ("generate_tool_arguments", "validate", "finish")
    assert any("rerun command" in item for item in first.trace_requirements)
