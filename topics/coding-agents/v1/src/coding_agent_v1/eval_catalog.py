from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


ALLOWED_TASK_CLASSES = frozenset({"fix", "feature", "rename", "diagnose", "resume"})
ALLOWED_SEVERITIES = frozenset({"smoke", "core", "stretch"})


@dataclass(slots=True, frozen=True)
class EvalScenarioSpec:
    scenario_id: str
    title: str
    task_class: str
    severity: str
    request: str
    expected_outcome: str
    failure_modes: tuple[str, ...]
    tags: tuple[str, ...]
    notes: str = ""
    setup_kind: str | None = None
    auto_approve_commands: bool = True
    planner_strategy: str = "deterministic_heuristic"
    available_tools: tuple[dict[str, str], ...] = ()
    expected_tool_sequence: tuple[str, ...] = ()
    expected_escalation_behavior: str = "not_needed"
    first_failure_state_if_broken: tuple[str, ...] = ()
    trace_requirements: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class EvalScenarioPack:
    pack_id: str
    title: str
    description: str
    scenarios: tuple[EvalScenarioSpec, ...]
    source_path: Path | None = None


@dataclass(slots=True, frozen=True)
class EvalScenarioPackSummary:
    pack_id: str
    title: str
    scenario_count: int
    task_class_counts: dict[str, int]
    severity_counts: dict[str, int]
    tag_counts: dict[str, int]
    failure_mode_counts: dict[str, int]
    source_path: Path | None = None


def load_eval_scenario_pack(path: Path) -> EvalScenarioPack:
    payload = json.loads(path.read_text(encoding="utf-8"))
    scenarios = tuple(_parse_scenario(item) for item in payload["scenarios"])
    return EvalScenarioPack(
        pack_id=str(payload["pack_id"]),
        title=str(payload["title"]),
        description=str(payload["description"]),
        scenarios=scenarios,
        source_path=path,
    )


def summarize_eval_scenario_pack(pack: EvalScenarioPack) -> str:
    summary = build_eval_scenario_pack_summary(pack)
    lines = [
        f"pack_id: {summary.pack_id}",
        f"title: {summary.title}",
        f"scenario_count: {summary.scenario_count}",
    ]
    if summary.source_path is not None:
        lines.append(f"source_path: {summary.source_path}")
    for label, counts in (
        ("task_classes", summary.task_class_counts),
        ("severities", summary.severity_counts),
        ("tags", summary.tag_counts),
        ("failure_modes", summary.failure_mode_counts),
    ):
        lines.append(f"{label}:")
        for key in sorted(counts):
            lines.append(f"  {key}: {counts[key]}")
    return "\n".join(lines)


def build_eval_scenario_pack_summary(pack: EvalScenarioPack) -> EvalScenarioPackSummary:
    task_class_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    tag_counts: dict[str, int] = {}
    failure_mode_counts: dict[str, int] = {}

    for scenario in pack.scenarios:
        _bump(task_class_counts, scenario.task_class)
        _bump(severity_counts, scenario.severity)
        for tag in scenario.tags:
            _bump(tag_counts, tag)
        for failure_mode in scenario.failure_modes:
            _bump(failure_mode_counts, failure_mode)

    return EvalScenarioPackSummary(
        pack_id=pack.pack_id,
        title=pack.title,
        scenario_count=len(pack.scenarios),
        task_class_counts=task_class_counts,
        severity_counts=severity_counts,
        tag_counts=tag_counts,
        failure_mode_counts=failure_mode_counts,
        source_path=pack.source_path,
    )


def list_executable_eval_scenarios(pack: EvalScenarioPack) -> tuple[EvalScenarioSpec, ...]:
    return tuple(scenario for scenario in pack.scenarios if scenario.setup_kind is not None)


def _parse_scenario(payload: dict[str, object]) -> EvalScenarioSpec:
    task_class = str(payload["task_class"])
    severity = str(payload["severity"])
    if task_class not in ALLOWED_TASK_CLASSES:
        raise ValueError(f"Unsupported task_class: {task_class}")
    if severity not in ALLOWED_SEVERITIES:
        raise ValueError(f"Unsupported severity: {severity}")

    failure_modes = tuple(str(item) for item in payload.get("failure_modes", []))
    tags = tuple(str(item) for item in payload.get("tags", []))
    if not failure_modes:
        raise ValueError(f"Scenario {payload.get('scenario_id')} must declare at least one failure mode")

    available_tools_payload = payload.get("available_tools", [])
    available_tools = (
        tuple(
            {
                "name": str(item["name"]),
                "kind": str(item["kind"]),
                "description": str(item.get("description", "")),
            }
            for item in available_tools_payload
        )
        if available_tools_payload
        else _default_available_tools(task_class)
    )

    return EvalScenarioSpec(
        scenario_id=str(payload["scenario_id"]),
        title=str(payload["title"]),
        task_class=task_class,
        severity=severity,
        request=str(payload["request"]),
        expected_outcome=str(payload["expected_outcome"]),
        failure_modes=failure_modes,
        tags=tags,
        notes=str(payload.get("notes", "")),
        setup_kind=str(payload["setup_kind"]) if payload.get("setup_kind") is not None else None,
        auto_approve_commands=bool(payload.get("auto_approve_commands", True)),
        planner_strategy=str(payload.get("planner_strategy", "deterministic_heuristic")),
        available_tools=available_tools,
        expected_tool_sequence=tuple(
            str(item) for item in payload.get("expected_tool_sequence", _default_tool_sequence(task_class))
        ),
        expected_escalation_behavior=str(payload.get("expected_escalation_behavior", "not_needed")),
        first_failure_state_if_broken=tuple(
            str(item) for item in payload.get("first_failure_state_if_broken", [])
        ),
        trace_requirements=tuple(str(item) for item in payload.get("trace_requirements", [])),
    )


def _default_available_tools(task_class: str) -> tuple[dict[str, str], ...]:
    if task_class == "resume":
        return (
            {"name": "read_memory", "kind": "read_only", "description": "Recall prior session state"},
            {"name": "read_file", "kind": "read_only", "description": "Inspect repo files"},
            {"name": "run_command", "kind": "command", "description": "Run validation"},
        )
    if task_class == "diagnose":
        return (
            {"name": "run_command", "kind": "command", "description": "Run validation"},
            {"name": "search_code", "kind": "read_only", "description": "Find failure evidence"},
            {"name": "edit_file", "kind": "file_edit", "description": "Apply bounded edits when allowed"},
        )
    return (
        {"name": "read_file", "kind": "read_only", "description": "Inspect source and tests"},
        {"name": "search_code", "kind": "read_only", "description": "Locate relevant code"},
        {"name": "edit_file", "kind": "file_edit", "description": "Apply bounded edits"},
        {"name": "run_command", "kind": "command", "description": "Run validation"},
    )


def _default_tool_sequence(task_class: str) -> tuple[str, ...]:
    if task_class == "fix":
        return ("run_command", "read_file", "edit_file", "run_command")
    if task_class == "feature":
        return ("search_code", "edit_file", "run_command")
    if task_class == "rename":
        return ("search_code", "edit_file", "run_command")
    if task_class == "diagnose":
        return ("run_command", "search_code")
    if task_class == "resume":
        return ("read_memory", "read_file")
    return ("read_file",)


def _bump(counts: dict[str, int], key: str) -> None:
    counts[key] = counts.get(key, 0) + 1
