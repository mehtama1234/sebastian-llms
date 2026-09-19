from __future__ import annotations

from pathlib import Path
from uuid import uuid4
import subprocess
import shlex
import json
import os
import re

from .models import (
    CompactContextArtifact,
    PermissionOutcome,
    HandoffArtifact,
    ProceduralRepairRecord,
    RepairProposal,
    SessionRecord,
    SessionStatus,
    TaskFlow,
    TaskPlan,
    ToolKind,
    ToolRequest,
    ToolResult,
    WorkingMemory,
)
from .behavior_index import infer_behavior_lookup
from .planner import (
    append_task_flow_candidate,
    count_symbol_occurrences,
    diagnose_reason,
    extract_cli_flag_request,
    extract_existing_test_file_reference,
    extract_existing_test_file_references,
    extract_env_var_request,
    extract_flag_token,
    extract_generic_cli_flag_request,
    extract_generic_env_var_request,
    extract_generic_option_request,
    extract_config_option_request,
    failure_report_reason,
    feature_reason,
    feature_workspace_score,
    find_cli_parser_files,
    find_config_mapping_files,
    find_python_test_paths,
    find_source_files_containing_symbol,
    fix_reason,
    inspect_reason,
    looks_like_diagnose_request,
    looks_like_failure_report_request,
    looks_like_fix_request,
    looks_like_inspect_request,
    looks_like_test_failure_context,
    rename_reason,
    DEFAULT_PLANNER_STRATEGY,
    MODEL_GUIDED_PLANNER_STRATEGY,
    PlannerConfigurationError,
    resolve_planner_backend,
    select_task_flow_from_candidates,
    select_feature_strategy,
)
from .permissions import decide_permission
from .session_store import SessionStore, summarize_task_plan, summarize_working_memory
from .tools import execute_tool, is_ignored_path
from .validator import summarize_validation
from .workspace import build_workspace_summary


def classify_task_flow(request: str) -> TaskFlow:
    lowered = request.lower()
    if _extract_rename_request(request) is not None:
        return TaskFlow.RENAME
    if (
        extract_cli_flag_request(request) is not None
        or extract_config_option_request(request) is not None
        or extract_env_var_request(request) is not None
    ):
        return TaskFlow.FEATURE
    if looks_like_diagnose_request(lowered):
        return TaskFlow.DIAGNOSE
    if looks_like_fix_request(lowered):
        return TaskFlow.FIX
    return TaskFlow.INSPECT
def _choose_validation_command(
    request: str,
    workspace_root: Path,
    task_flow: TaskFlow,
    *,
    feature_strategy: str = "",
    feature_arguments: dict[str, str] | None = None,
) -> str:
    if task_flow is TaskFlow.INSPECT:
        return ""
    feature_arguments = feature_arguments or {}
    test_paths = find_python_test_paths(workspace_root)
    referenced_tests = extract_existing_test_file_references(request, workspace_root)
    if referenced_tests:
        return _build_pytest_command_for_paths(referenced_tests, workspace_root, max_paths=None)
    if task_flow is TaskFlow.FEATURE:
        if feature_strategy == "cli_flag" and feature_arguments.get("flag_name"):
            flag_name = feature_arguments["flag_name"]
            matching_tests = _find_test_files_containing_patterns(test_paths, [flag_name])
            if matching_tests:
                return _build_pytest_command_for_paths(matching_tests, workspace_root)
            related_tests = _find_test_files_for_source_modules(
                test_paths,
                workspace_root,
                find_cli_parser_files(workspace_root),
            )
            if related_tests:
                return _build_pytest_command_for_paths(related_tests, workspace_root)
        if feature_strategy == "config_option" and feature_arguments.get("option_name"):
            option_name = feature_arguments["option_name"]
            matching_tests = _find_test_files_containing_patterns(test_paths, [option_name])
            if matching_tests:
                return _build_pytest_command_for_paths(matching_tests, workspace_root)
            related_tests = _find_test_files_for_source_modules(
                test_paths,
                workspace_root,
                find_config_mapping_files(workspace_root),
            )
            if related_tests:
                return _build_pytest_command_for_paths(related_tests, workspace_root)
        if feature_strategy == "env_var" and feature_arguments.get("env_name") and feature_arguments.get(
            "option_name"
        ):
            env_name = feature_arguments["env_name"]
            option_name = feature_arguments["option_name"]
            matching_tests = _find_test_files_containing_patterns(test_paths, [env_name, option_name])
            if matching_tests:
                return _build_pytest_command_for_paths(matching_tests, workspace_root)
            related_tests = _find_test_files_for_source_modules(
                test_paths,
                workspace_root,
                find_config_mapping_files(workspace_root, require_env_var=True),
            )
            if related_tests:
                return _build_pytest_command_for_paths(related_tests, workspace_root)
    if task_flow is TaskFlow.RENAME:
        rename_request = _extract_rename_request(request)
        if rename_request is not None:
            old_name, _ = rename_request
            matching_tests = _find_test_files_containing_patterns(test_paths, [old_name])
            if matching_tests:
                return _build_pytest_command_for_paths(matching_tests, workspace_root)
            related_tests = _find_test_files_for_source_modules(
                test_paths,
                workspace_root,
                find_source_files_containing_symbol(workspace_root, old_name),
            )
            if related_tests:
                return _build_pytest_command_for_paths(related_tests, workspace_root)
    python_tests = [path.relative_to(workspace_root) for path in test_paths]
    if not python_tests:
        return ""
    if task_flow in {TaskFlow.FEATURE, TaskFlow.RENAME} and len(python_tests) == 1:
        return _build_pytest_command_for_relative_paths(python_tests)
    return "pytest -q"


def _find_test_files_containing_patterns(
    test_paths: list[Path],
    patterns: list[str],
) -> list[Path]:
    matches: list[Path] = []
    lowered_patterns = [pattern.lower() for pattern in patterns if pattern]
    for path in test_paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            continue
        if all(pattern in text for pattern in lowered_patterns):
            matches.append(path)
    return matches


def _build_pytest_command_for_paths(
    paths: list[Path],
    workspace_root: Path,
    *,
    max_paths: int | None = 3,
) -> str:
    selected_paths = paths if max_paths is None else paths[:max_paths]
    selected = [path.relative_to(workspace_root) for path in selected_paths]
    return _build_pytest_command_for_relative_paths(selected)


def _build_pytest_command_for_relative_paths(relative_paths: list[Path]) -> str:
    selected = [shlex.quote(str(path)) for path in relative_paths]
    prefix = "PYTHONPATH=. " if any(path.parent != Path(".") for path in relative_paths) else ""
    return f"{prefix}pytest -q {' '.join(selected)}"


def _find_test_files_for_source_modules(
    test_paths: list[Path],
    workspace_root: Path,
    source_paths: list[Path],
) -> list[Path]:
    scored_matches: list[tuple[int, Path]] = []
    for test_path in test_paths:
        try:
            text = test_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        score = 0
        lowered_text = text.lower()
        lowered_test_name = test_path.stem.lower()
        for source_path in source_paths:
            module_name = _module_name_for_path(source_path, workspace_root)
            if not module_name:
                continue
            module_stem = source_path.stem.lower()
            if f"from {module_name} import" in text or f"import {module_name}" in text:
                score += 3
            if module_stem and module_stem in lowered_test_name:
                score += 2
            if module_stem and f"import {module_stem}" in lowered_text:
                score += 1
        if score > 0:
            scored_matches.append((score, test_path))
    scored_matches.sort(key=lambda item: (-item[0], item[1].name))
    return [path for _, path in scored_matches[:3]]


def _module_name_for_path(path: Path, workspace_root: Path) -> str:
    relative = path.relative_to(workspace_root).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def build_task_plan(
    request: str,
    workspace_root: Path,
    instruction_files: list[str],
    *,
    planner_strategy: str | None = None,
) -> TaskPlan:
    backend = resolve_planner_backend(planner_strategy)
    baseline_strategy = (
        DEFAULT_PLANNER_STRATEGY
        if backend.strategy == MODEL_GUIDED_PLANNER_STRATEGY
        else backend.strategy
    )
    baseline_reason = (
        "deterministic heuristic planner computed as the model-guided baseline"
        if backend.strategy == MODEL_GUIDED_PLANNER_STRATEGY
        else backend.reason
    )
    baseline_plan = _build_deterministic_task_plan(
        request,
        workspace_root,
        instruction_files,
        planner_strategy=baseline_strategy,
        planner_strategy_reason=baseline_reason,
    )
    if backend.strategy != MODEL_GUIDED_PLANNER_STRATEGY:
        return baseline_plan
    return _build_model_guided_task_plan(
        request,
        workspace_root,
        instruction_files,
        baseline_plan=baseline_plan,
        command=backend.command,
        planner_strategy_reason=backend.reason,
    )


def _build_deterministic_task_plan(
    request: str,
    workspace_root: Path,
    instruction_files: list[str],
    *,
    planner_strategy: str,
    planner_strategy_reason: str,
) -> TaskPlan:
    task_flow, flow_reasons, feature_strategy, feature_arguments, strategy_reason = _select_task_flow(
        request,
        workspace_root,
        instruction_files,
    )
    reasons = list(flow_reasons)
    if task_flow is TaskFlow.FEATURE:
        if strategy_reason:
            reasons.append(strategy_reason)
    validation_command = _choose_validation_command(
        request,
        workspace_root,
        task_flow,
        feature_strategy=feature_strategy,
        feature_arguments=feature_arguments,
    )
    behavior_lookup = infer_behavior_lookup(
        request,
        workspace_root,
        task_flow,
        feature_strategy=feature_strategy,
        validation_command=validation_command,
    )
    if behavior_lookup.behavior_ids:
        reasons.append(
            "behavior index selected affected behavior(s): "
            + ", ".join(f"`{behavior_id}`" for behavior_id in behavior_lookup.behavior_ids)
        )
    if behavior_lookup.stale_behavior_ids:
        reasons.append(
            "behavior index has stale source anchor(s): "
            + ", ".join(f"`{behavior_id}`" for behavior_id in behavior_lookup.stale_behavior_ids)
        )
    if validation_command:
        reasons.append(
            _validation_reason(
                request,
                workspace_root,
                task_flow,
                validation_command,
                feature_strategy=feature_strategy,
                feature_arguments=feature_arguments,
            )
        )
    else:
        reasons.append("no validation command selected for the current flow and workspace evidence")
    initial_actions = build_initial_actions(
        request,
        workspace_root,
        instruction_files,
        task_flow,
        feature_strategy=feature_strategy,
        feature_arguments=feature_arguments,
        validation_command=validation_command,
    )
    return TaskPlan(
        task_flow=task_flow,
        planner_strategy=planner_strategy,
        planner_strategy_reason=planner_strategy_reason,
        feature_strategy=feature_strategy,
        feature_arguments=feature_arguments,
        affected_behavior_ids=behavior_lookup.behavior_ids,
        implementation_surfaces=behavior_lookup.source_files,
        initial_actions=[action.name for action in initial_actions],
        validation_command=validation_command,
        reasons=reasons,
    )


def _build_model_guided_task_plan(
    request: str,
    workspace_root: Path,
    instruction_files: list[str],
    *,
    baseline_plan: TaskPlan,
    command: str,
    planner_strategy_reason: str,
) -> TaskPlan:
    payload = {
        "request": request,
        "workspace_root": str(workspace_root),
        "instruction_files": instruction_files,
        "deterministic_baseline": _task_plan_to_model_payload(baseline_plan),
        "contract": {
            "required_fields": ["task_flow", "reasons"],
            "allowed_task_flows": [item.value for item in TaskFlow],
            "optional_fields": ["feature_strategy", "feature_arguments"],
            "note": "The harness recomputes behavior IDs, implementation surfaces, validation command, and initial actions.",
        },
    }
    model_decision = _run_model_planner_command(command, payload)
    task_flow = _parse_model_task_flow(model_decision)
    reasons = _parse_model_reasons(model_decision)
    feature_strategy = str(model_decision.get("feature_strategy", ""))
    feature_arguments = _parse_model_feature_arguments(model_decision)
    if task_flow is TaskFlow.FEATURE and not feature_strategy:
        feature_strategy = baseline_plan.feature_strategy
        feature_arguments = dict(baseline_plan.feature_arguments)
        reasons.append("model planner omitted feature strategy; deterministic feature strategy was reused")
    validation_command = _choose_validation_command(
        request,
        workspace_root,
        task_flow,
        feature_strategy=feature_strategy,
        feature_arguments=feature_arguments,
    )
    behavior_lookup = infer_behavior_lookup(
        request,
        workspace_root,
        task_flow,
        feature_strategy=feature_strategy,
        validation_command=validation_command,
    )
    if behavior_lookup.behavior_ids:
        reasons.append(
            "behavior index selected affected behavior(s): "
            + ", ".join(f"`{behavior_id}`" for behavior_id in behavior_lookup.behavior_ids)
        )
    if validation_command:
        reasons.append(
            _validation_reason(
                request,
                workspace_root,
                task_flow,
                validation_command,
                feature_strategy=feature_strategy,
                feature_arguments=feature_arguments,
            )
        )
    else:
        reasons.append("no validation command selected for the current flow and workspace evidence")
    initial_actions = build_initial_actions(
        request,
        workspace_root,
        instruction_files,
        task_flow,
        feature_strategy=feature_strategy,
        feature_arguments=feature_arguments,
        validation_command=validation_command,
    )
    return TaskPlan(
        task_flow=task_flow,
        planner_strategy=MODEL_GUIDED_PLANNER_STRATEGY,
        planner_strategy_reason=planner_strategy_reason,
        feature_strategy=feature_strategy,
        feature_arguments=feature_arguments,
        affected_behavior_ids=behavior_lookup.behavior_ids,
        implementation_surfaces=behavior_lookup.source_files,
        initial_actions=[action.name for action in initial_actions],
        validation_command=validation_command,
        reasons=[
            f"model planner command selected `{task_flow.value}` from validated JSON output",
            f"deterministic baseline task_flow was `{baseline_plan.task_flow.value}`",
            *reasons,
        ],
    )


def _run_model_planner_command(command: str, payload: dict[str, object]) -> dict[str, object]:
    try:
        timeout_seconds = float(os.environ.get("CODING_AGENT_V1_MODEL_PLANNER_TIMEOUT_SECONDS", "20"))
        completed = subprocess.run(
            shlex.split(command),
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PlannerConfigurationError(
            f"model planner command failed before planning completed: {exc}; no tool action was taken"
        ) from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        raise PlannerConfigurationError(
            f"model planner command failed: {detail}; no tool action was taken"
        )
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise PlannerConfigurationError(
            "model planner command did not return valid JSON on stdout; no tool action was taken"
        ) from exc
    if not isinstance(parsed, dict):
        raise PlannerConfigurationError(
            "model planner command must return a JSON object; no tool action was taken"
        )
    return parsed


def _parse_model_task_flow(model_decision: dict[str, object]) -> TaskFlow:
    raw_task_flow = model_decision.get("task_flow")
    if not isinstance(raw_task_flow, str):
        raise PlannerConfigurationError(
            "model planner output must include string field `task_flow`; no tool action was taken"
        )
    try:
        return TaskFlow(raw_task_flow)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in TaskFlow)
        raise PlannerConfigurationError(
            f"model planner output has unsupported task_flow `{raw_task_flow}`; expected one of: {allowed}; "
            "no tool action was taken"
        ) from exc


def _parse_model_reasons(model_decision: dict[str, object]) -> list[str]:
    raw_reasons = model_decision.get("reasons")
    if isinstance(raw_reasons, str):
        raw_reasons = [raw_reasons]
    if not isinstance(raw_reasons, list) or not raw_reasons:
        raise PlannerConfigurationError(
            "model planner output must include non-empty `reasons`; no tool action was taken"
        )
    reasons = [str(item) for item in raw_reasons if str(item).strip()]
    if not reasons:
        raise PlannerConfigurationError(
            "model planner output `reasons` must contain at least one non-empty item; no tool action was taken"
        )
    return reasons


def _parse_model_feature_arguments(model_decision: dict[str, object]) -> dict[str, str]:
    raw_arguments = model_decision.get("feature_arguments", {})
    if raw_arguments is None:
        return {}
    if not isinstance(raw_arguments, dict):
        raise PlannerConfigurationError(
            "model planner output `feature_arguments` must be a JSON object; no tool action was taken"
        )
    return {str(key): str(value) for key, value in raw_arguments.items()}


def _task_plan_to_model_payload(plan: TaskPlan) -> dict[str, object]:
    return {
        "task_flow": plan.task_flow.value,
        "planner_strategy": plan.planner_strategy,
        "planner_strategy_reason": plan.planner_strategy_reason,
        "feature_strategy": plan.feature_strategy,
        "feature_arguments": plan.feature_arguments,
        "affected_behavior_ids": plan.affected_behavior_ids,
        "implementation_surfaces": plan.implementation_surfaces,
        "initial_actions": plan.initial_actions,
        "validation_command": plan.validation_command,
        "reasons": plan.reasons,
    }


def _validation_reason(
    request: str,
    workspace_root: Path,
    task_flow: TaskFlow,
    validation_command: str,
    *,
    feature_strategy: str = "",
    feature_arguments: dict[str, str] | None = None,
) -> str:
    referenced_tests = extract_existing_test_file_references(request, workspace_root)
    if referenced_tests:
        if len(referenced_tests) == 1:
            detail = f"explicit referenced test `{referenced_tests[0].name}`"
        else:
            names = ", ".join(f"`{path.name}`" for path in referenced_tests)
            detail = f"explicit referenced tests {names}"
        return f"selected validation command `{validation_command}` from {detail}"
    feature_arguments = feature_arguments or {}
    test_paths = find_python_test_paths(workspace_root)
    if task_flow is TaskFlow.FEATURE:
        if feature_strategy == "cli_flag" and feature_arguments.get("flag_name"):
            flag_name = feature_arguments["flag_name"]
            matching_tests = _find_test_files_containing_patterns(test_paths, [flag_name])
            if matching_tests and _build_pytest_command_for_paths(matching_tests, workspace_root) == validation_command:
                return f"selected validation command `{validation_command}` from matching test content for `{flag_name}`"
            related_tests = _find_test_files_for_source_modules(
                test_paths,
                workspace_root,
                find_cli_parser_files(workspace_root),
            )
            if related_tests and _build_pytest_command_for_paths(related_tests, workspace_root) == validation_command:
                return f"selected validation command `{validation_command}` from module-aware CLI parser test evidence"
        if feature_strategy == "config_option" and feature_arguments.get("option_name"):
            option_name = feature_arguments["option_name"]
            matching_tests = _find_test_files_containing_patterns(test_paths, [option_name])
            if matching_tests and _build_pytest_command_for_paths(matching_tests, workspace_root) == validation_command:
                return (
                    f"selected validation command `{validation_command}` "
                    f"from matching test content for config option `{option_name}`"
                )
            related_tests = _find_test_files_for_source_modules(
                test_paths,
                workspace_root,
                find_config_mapping_files(workspace_root),
            )
            if related_tests and _build_pytest_command_for_paths(related_tests, workspace_root) == validation_command:
                return f"selected validation command `{validation_command}` from module-aware config test evidence"
        if feature_strategy == "env_var" and feature_arguments.get("env_name") and feature_arguments.get("option_name"):
            env_name = feature_arguments["env_name"]
            option_name = feature_arguments["option_name"]
            matching_tests = _find_test_files_containing_patterns(test_paths, [env_name, option_name])
            if matching_tests and _build_pytest_command_for_paths(matching_tests, workspace_root) == validation_command:
                return (
                    f"selected validation command `{validation_command}` "
                    f"from matching test content for env var `{env_name}` and option `{option_name}`"
                )
            related_tests = _find_test_files_for_source_modules(
                test_paths,
                workspace_root,
                find_config_mapping_files(workspace_root, require_env_var=True),
            )
            if related_tests and _build_pytest_command_for_paths(related_tests, workspace_root) == validation_command:
                return (
                    f"selected validation command `{validation_command}` "
                    f"from module-aware environment-config test evidence"
                )
    if task_flow is TaskFlow.RENAME:
        rename_request = _extract_rename_request(request)
        if rename_request is not None:
            old_name, _ = rename_request
            matching_tests = _find_test_files_containing_patterns(test_paths, [old_name])
            if matching_tests and _build_pytest_command_for_paths(matching_tests, workspace_root) == validation_command:
                return f"selected validation command `{validation_command}` from matching rename target `{old_name}` test evidence"
            related_tests = _find_test_files_for_source_modules(
                test_paths,
                workspace_root,
                find_source_files_containing_symbol(workspace_root, old_name),
            )
            if related_tests and _build_pytest_command_for_paths(related_tests, workspace_root) == validation_command:
                return f"selected validation command `{validation_command}` from module-aware rename test evidence"
    python_tests = [path.relative_to(workspace_root) for path in test_paths]
    if task_flow in {TaskFlow.FEATURE, TaskFlow.RENAME} and len(python_tests) == 1:
        single_test_command = _build_pytest_command_for_relative_paths(python_tests)
        if single_test_command == validation_command:
            return f"selected validation command `{validation_command}` from single-test workspace fallback"
    if validation_command == "pytest -q" and test_paths:
        return f"selected validation command `{validation_command}` from full-suite fallback because no narrower test target was justified"
    return f"selected validation command `{validation_command}` from workspace test evidence"


def _select_task_flow(
    request: str,
    workspace_root: Path,
    instruction_files: list[str],
) -> tuple[TaskFlow, list[str], str, dict[str, str], str]:
    lowered = request.lower()
    feature_strategy, feature_arguments, strategy_reason = select_feature_strategy(request, workspace_root)
    scored_candidates = []
    test_paths = find_python_test_paths(workspace_root)
    has_tests = bool(test_paths)
    referenced_tests = extract_existing_test_file_references(request, workspace_root)

    rename_request = _extract_rename_request(request)
    if rename_request is not None:
        old_name, _ = rename_request
        rename_matches = count_symbol_occurrences(workspace_root, old_name)
        append_task_flow_candidate(
            scored_candidates,
            task_flow=TaskFlow.RENAME,
            score=12 + min(rename_matches, 3),
            priority=0,
            reason=rename_reason(old_name, rename_matches),
        )

    if feature_strategy:
        feature_score = 11 if strategy_reason.startswith("feature strategy selected") else 8
        cli_parser_count = len(find_cli_parser_files(workspace_root))
        config_mapping_count = len(find_config_mapping_files(workspace_root))
        env_config_mapping_count = len(find_config_mapping_files(workspace_root, require_env_var=True))
        feature_score += feature_workspace_score(
            feature_strategy,
            cli_parser_count=cli_parser_count,
            config_mapping_count=config_mapping_count,
            env_config_mapping_count=env_config_mapping_count,
        )
        append_task_flow_candidate(
            scored_candidates,
            task_flow=TaskFlow.FEATURE,
            score=feature_score,
            priority=1,
            reason=feature_reason(
                feature_strategy,
                strategy_reason,
                cli_parser_count=cli_parser_count,
                config_mapping_count=config_mapping_count,
                env_config_mapping_count=env_config_mapping_count,
            ),
        )

    if looks_like_diagnose_request(lowered):
        diagnose_score = 9 if any(term in lowered for term in ("diagnose", "why", "investigate", "debug")) else 7
        if has_tests:
            diagnose_score += 1
        if referenced_tests:
            diagnose_score += 2
        append_task_flow_candidate(
            scored_candidates,
            task_flow=TaskFlow.DIAGNOSE,
            score=diagnose_score,
            priority=2,
            reason=diagnose_reason(has_tests, referenced_tests),
        )

    if looks_like_fix_request(lowered):
        fix_score = 9 if any(term in lowered for term in ("fix", "repair", "resolve")) else 7
        if has_tests:
            fix_score += 1
        if referenced_tests:
            fix_score += 2
        append_task_flow_candidate(
            scored_candidates,
            task_flow=TaskFlow.FIX,
            score=fix_score,
            priority=3,
            reason=fix_reason(has_tests, referenced_tests),
        )

    if looks_like_failure_report_request(lowered) and has_tests:
        diagnose_score = 6
        if referenced_tests:
            diagnose_score += 2
        append_task_flow_candidate(
            scored_candidates,
            task_flow=TaskFlow.DIAGNOSE,
            score=diagnose_score,
            priority=4,
            reason=failure_report_reason(referenced_tests),
        )

    if "run" in lowered and "test" in lowered and "report" in lowered:
        append_task_flow_candidate(
            scored_candidates,
            task_flow=TaskFlow.DIAGNOSE,
            score=10,
            priority=2,
            reason="diagnose evidence: request asks to run tests and report the result",
        )
    if looks_like_inspect_request(lowered):
        inspect_score = 6
        if instruction_files:
            inspect_score += 1
        append_task_flow_candidate(
            scored_candidates,
            task_flow=TaskFlow.INSPECT,
            score=inspect_score,
            priority=5,
            reason=inspect_reason(instruction_files),
        )

    task_flow, reasons = select_task_flow_from_candidates(scored_candidates)
    if task_flow is not TaskFlow.FEATURE:
        feature_strategy = ""
        feature_arguments = {}
        strategy_reason = ""
    return task_flow, reasons, feature_strategy, feature_arguments, strategy_reason
def build_initial_actions(
    request: str,
    workspace_root: Path,
    instruction_files: list[str],
    task_flow: TaskFlow,
    *,
    feature_strategy: str,
    feature_arguments: dict[str, str],
    validation_command: str,
) -> list[ToolRequest]:
    actions: list[ToolRequest] = []
    read_target = instruction_files[0] if instruction_files else "README.md"
    if (workspace_root / read_target).exists():
        actions.append(
            ToolRequest(
                name="read_file",
                kind=ToolKind.READ_ONLY,
                target=str(workspace_root / read_target),
                args={"max_chars": "3000"},
            )
        )

    if task_flow is TaskFlow.RENAME:
        rename_request = _extract_rename_request(request)
        if rename_request is not None:
            actions.append(
                ToolRequest(
                    name="search_code",
                    kind=ToolKind.READ_ONLY,
                    target=str(workspace_root),
                    args={"pattern": rename_request[0], "max_hits": "20"},
                )
            )
        return actions

    if task_flow is TaskFlow.FEATURE:
        if feature_strategy == "env_var":
            env_name = feature_arguments["env_name"]
            actions.append(
                ToolRequest(
                    name="search_code",
                    kind=ToolKind.READ_ONLY,
                    target=str(workspace_root),
                    args={"pattern": env_name, "max_hits": "20"},
                )
            )
            return actions
        if feature_strategy == "config_option":
            actions.append(
                ToolRequest(
                    name="search_code",
                    kind=ToolKind.READ_ONLY,
                    target=str(workspace_root),
                    args={"pattern": feature_arguments["option_name"], "max_hits": "20"},
                )
            )
            return actions
        if feature_strategy == "cli_flag":
            actions.append(
                ToolRequest(
                    name="search_code",
                    kind=ToolKind.READ_ONLY,
                    target=str(workspace_root),
                    args={"pattern": "ArgumentParser", "max_hits": "20"},
                )
            )
        return actions

    if task_flow in {TaskFlow.FIX, TaskFlow.DIAGNOSE}:
        if validation_command:
            actions.append(
                ToolRequest(
                    name="run_command",
                    kind=ToolKind.COMMAND,
                    target=str(workspace_root),
                    args={"command": validation_command, "timeout_seconds": "15", "max_chars": "4000"},
                )
            )
        return actions

    lowered = request.lower()
    if "search" in lowered or "find" in lowered:
        actions.append(
            ToolRequest(
                name="search_code",
                kind=ToolKind.READ_ONLY,
                target=str(workspace_root),
                args={"pattern": _extract_pattern(request), "max_hits": "20"},
            )
        )
        return actions

    return actions


def _extract_pattern(request: str) -> str:
    quoted = shlex.split(request)
    if len(quoted) > 1:
        return quoted[-1]
    return request.strip()


def _extract_rename_request(request: str) -> tuple[str, str] | None:
    patterns = [
        r"\brename\s+([A-Za-z_][A-Za-z0-9_]*)\s+to\s+([A-Za-z_][A-Za-z0-9_]*)\b",
        r"\brename\s+(?:the\s+)?([A-Za-z_][A-Za-z0-9_]*)\s+function\s+to\s+([A-Za-z_][A-Za-z0-9_]*)\b",
        r"\brename\s+([A-Za-z_][A-Za-z0-9_]*)\s*->\s*([A-Za-z_][A-Za-z0-9_]*)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, request, flags=re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)
    return None


def _extract_failure_hints(output: str) -> list[str]:
    hints: list[str] = []
    failed_tests = re.findall(r"FAILED\s+([^\s:]+)", output)
    hints.extend(failed_tests)
    file_refs = re.findall(r"([A-Za-z0-9_./-]+\.py)", output)
    for ref in file_refs:
        if ref not in hints:
            hints.append(ref)
    return hints[:3]


def _build_follow_up_actions(validation_result: ToolResult, workspace_root: Path) -> list[ToolRequest]:
    if validation_result.ok:
        return []
    hints = _extract_failure_hints(validation_result.output)
    actions: list[ToolRequest] = []
    for hint in hints:
        pattern = Path(hint).stem.replace("test_", "")
        if not pattern:
            continue
        actions.append(
            ToolRequest(
                name="search_code",
                kind=ToolKind.READ_ONLY,
                target=str(workspace_root),
                args={"pattern": pattern, "max_hits": "10"},
            )
        )
    return actions


def _collect_cli_flag_proposals(
    workspace_root: Path,
    flag_name: str,
) -> list[RepairProposal]:
    proposals: list[RepairProposal] = []
    for path in sorted(workspace_root.rglob("*.py")):
        if is_ignored_path(path, workspace_root):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "ArgumentParser(" not in text:
            continue
        if f"'{flag_name}'" in text or f'"{flag_name}"' in text:
            continue
        parser_assignment = re.search(
            r"^([ \t]*parser\s*=\s*argparse\.ArgumentParser\(.*\))$",
            text,
            flags=re.MULTILINE,
        )
        if not parser_assignment:
            continue
        anchor = parser_assignment.group(1)
        indentation = re.match(r"^([ \t]*)", anchor).group(1)
        new_line = (
            f'{anchor}\n'
            f'{indentation}parser.add_argument("{flag_name}", action="store_true", '
            f'help="Enable {flag_name[2:]} mode.")'
        )
        rel = str(path.relative_to(workspace_root))
        proposals.append(
            RepairProposal(
                file=rel,
                old_text=anchor,
                new_text=new_line,
                reason=(
                    f"Request explicitly asks to add the `{flag_name}` CLI flag, "
                    f"and `{rel}` defines an `argparse.ArgumentParser` without that flag."
                ),
                score=12,
                evidence=[
                    f"feature-request:cli-flag:{flag_name}",
                    f"parser-file:{rel}",
                ],
            )
        )
    return proposals


def _collect_config_option_proposals(
    workspace_root: Path,
    option_name: str,
    value_literal: str,
) -> list[RepairProposal]:
    proposals: list[RepairProposal] = []
    assignment_pattern = re.compile(
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{(.*?)\}",
        flags=re.MULTILINE | re.DOTALL,
    )
    for path in sorted(workspace_root.rglob("*.py")):
        if is_ignored_path(path, workspace_root):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in assignment_pattern.finditer(text):
            variable_name = match.group(1)
            if not re.search(r"(config|settings|options)", variable_name, flags=re.IGNORECASE):
                continue
            old_assignment = match.group(0)
            if re.search(rf"['\"]{re.escape(option_name)}['\"]\s*:", old_assignment):
                continue
            new_assignment = _add_config_option_to_assignment(old_assignment, option_name, value_literal)
            if new_assignment == old_assignment:
                continue
            rel = str(path.relative_to(workspace_root))
            proposals.append(
                RepairProposal(
                    file=rel,
                    old_text=old_assignment,
                    new_text=new_assignment,
                    reason=(
                        f"Request explicitly asks to add the `{option_name}` config option with default "
                        f"`{value_literal}`, and `{rel}` defines the config-style mapping `{variable_name}`."
                    ),
                    score=11,
                    evidence=[
                        f"feature-request:config-option:{option_name}",
                        f"default-value:{value_literal}",
                        f"config-mapping:{variable_name}",
                        f"file:{rel}",
                    ],
                )
            )
    return proposals


def _collect_env_var_config_proposals(
    workspace_root: Path,
    env_name: str,
    option_name: str,
    value_literal: str,
) -> list[RepairProposal]:
    proposals: list[RepairProposal] = []
    assignment_pattern = re.compile(
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{(.*?)\}",
        flags=re.MULTILINE | re.DOTALL,
    )
    for path in sorted(workspace_root.rglob("*.py")):
        if is_ignored_path(path, workspace_root):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "import os" not in text and "os.getenv(" not in text:
            continue
        for match in assignment_pattern.finditer(text):
            variable_name = match.group(1)
            if not re.search(r"(config|settings|options)", variable_name, flags=re.IGNORECASE):
                continue
            old_assignment = match.group(0)
            if re.search(rf"['\"]{re.escape(option_name)}['\"]\s*:", old_assignment):
                continue
            new_assignment = _add_config_option_to_assignment(
                old_assignment,
                option_name,
                f'os.getenv("{env_name}", {value_literal})',
            )
            if new_assignment == old_assignment:
                continue
            rel = str(path.relative_to(workspace_root))
            proposals.append(
                RepairProposal(
                    file=rel,
                    old_text=old_assignment,
                    new_text=new_assignment,
                    reason=(
                        f"Request explicitly asks to add the `{env_name}` environment variable with default "
                        f"`{value_literal}`, and `{rel}` defines the config-style mapping `{variable_name}` with `os` available."
                    ),
                    score=12,
                    evidence=[
                        f"feature-request:env-var:{env_name}",
                        f"config-option:{option_name}",
                        f"default-value:{value_literal}",
                        f"config-mapping:{variable_name}",
                        f"file:{rel}",
                    ],
                )
            )
    return proposals


def _add_config_option_to_assignment(assignment: str, option_name: str, value_literal: str) -> str:
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{(.*?)\}$", assignment, flags=re.DOTALL)
    if not match:
        return assignment
    variable_name = match.group(1)
    body = match.group(2)
    entry = f'"{option_name}": {value_literal}'
    if "\n" in body:
        stripped_body = body.rstrip()
        if stripped_body.strip():
            if not stripped_body.rstrip().endswith(","):
                stripped_body = stripped_body.rstrip() + ","
            new_body = f"{stripped_body}\n    {entry},\n"
        else:
            new_body = f"\n    {entry},\n"
        return f"{variable_name} = {{{new_body}}}"
    items = body.strip()
    new_items = f"{items}, {entry}" if items else entry
    return f"{variable_name} = {{{new_items}}}"


def _feature_proposals_to_actions(
    proposals: list[RepairProposal],
    workspace_root: Path,
    *,
    validation_command: str,
) -> list[ToolRequest]:
    actions = [
        ToolRequest(
            name="edit_file",
            kind=ToolKind.FILE_EDIT,
            target=str(workspace_root / proposal.file),
            args={"old_text": proposal.old_text, "new_text": proposal.new_text},
        )
        for proposal in proposals
    ]
    if validation_command:
        actions.append(
            ToolRequest(
                name="run_command",
                kind=ToolKind.COMMAND,
                target=str(workspace_root),
                args={"command": validation_command, "timeout_seconds": "15", "max_chars": "4000"},
            )
        )
    return actions


def _collect_symbol_rename_proposals(
    workspace_root: Path,
    old_name: str,
    new_name: str,
) -> list[RepairProposal]:
    proposals: list[RepairProposal] = []
    pattern = re.compile(rf"\b{re.escape(old_name)}\b")
    for path in sorted(workspace_root.rglob("*")):
        if not path.is_file() or is_ignored_path(path, workspace_root):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        match_count = len(pattern.findall(text))
        if match_count == 0:
            continue
        rel = str(path.relative_to(workspace_root))
        evidence = [
            f"rename-symbol:{old_name}->{new_name}",
            f"match-count:{match_count}",
            f"file:{rel}",
        ]
        proposals.append(
            RepairProposal(
                file=rel,
                old_text=old_name,
                new_text=new_name,
                reason=(
                    f"Request explicitly asks to rename `{old_name}` to `{new_name}`, "
                    f"and `{rel}` contains {match_count} exact symbol occurrence(s)."
                ),
                score=10 + match_count,
                evidence=evidence,
            )
        )
    return proposals


def _rename_proposals_to_actions(
    proposals: list[RepairProposal],
    workspace_root: Path,
    *,
    validation_command: str,
) -> list[ToolRequest]:
    actions = [
        ToolRequest(
            name="rename_symbol_in_file",
            kind=ToolKind.FILE_EDIT,
            target=str(workspace_root / proposal.file),
            args={"old_name": proposal.old_text, "new_name": proposal.new_text},
        )
        for proposal in proposals
    ]
    if validation_command:
        actions.append(
            ToolRequest(
                name="run_command",
                kind=ToolKind.COMMAND,
                target=str(workspace_root),
                args={"command": validation_command, "timeout_seconds": "15", "max_chars": "4000"},
            )
        )
    return actions


def _workspace_has_pytest_suite(workspace_root: Path) -> bool:
    for path in workspace_root.rglob("*.py"):
        if is_ignored_path(path, workspace_root):
            continue
        if path.name.startswith("test_") or path.name.endswith("_test.py"):
            return True
    return False


def _expected_operator(function_name: str) -> str | None:
    lowered = function_name.lower()
    if "add" in lowered or "sum" in lowered:
        return "+"
    if "sub" in lowered or "minus" in lowered:
        return "-"
    if "mul" in lowered or "prod" in lowered:
        return "*"
    if "div" in lowered:
        return "/"
    return None


def _extract_expected_literal(test_text: str, callable_name: str) -> str | None:
    patterns = [
        rf"assert\s+{re.escape(callable_name)}\([^)]*\)\s*==\s*([\"'][^\"']*[\"']|\d+(?:\.\d+)?)",
        rf"assert\s+{re.escape(callable_name)}\([^)]*\)\s*is\s*(True|False|None)",
    ]
    for pattern in patterns:
        match = re.search(pattern, test_text)
        if match:
            return match.group(1)
    return None


def _extract_asserted_callables(test_text: str) -> set[str]:
    matches = re.findall(r"assert\s+([A-Za-z_][A-Za-z0-9_\.]*)\(", test_text)
    return set(matches)


def _score_proposal(
    *,
    callable_name: str,
    module_name: str,
    asserted_callables: set[str],
    test_file: Path,
    proposal_kind: str,
) -> tuple[int, list[str]]:
    score = 0
    evidence: list[str] = []
    if callable_name in asserted_callables:
        score += 5
        evidence.append(f"asserted-callable:{callable_name}")
    if proposal_kind == "operator":
        score += 2
        evidence.append("behavior-match:operator")
    if proposal_kind == "literal":
        score += 2
        evidence.append("behavior-match:literal")
    if proposal_kind == "constant":
        score += 2
        evidence.append("behavior-match:constant")
    score += 1
    evidence.append(f"test-file:{test_file.name}")
    evidence.append(f"source-module:{module_name}")
    return score, evidence


def _from_import_targets(test_text: str) -> list[tuple[str, str, str]]:
    targets: list[tuple[str, str, str]] = []
    imports = re.findall(
        r"from\s+([A-Za-z_][A-Za-z0-9_]*)\s+import\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?",
        test_text,
    )
    for module_name, function_name, alias in imports:
        callable_name = alias or function_name
        targets.append((module_name, function_name, callable_name))
    return targets


def _module_import_targets(test_text: str) -> list[tuple[str, str, str]]:
    targets: list[tuple[str, str, str]] = []
    imports = re.findall(
        r"import\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?",
        test_text,
    )
    asserted_callables = _extract_asserted_callables(test_text)
    for module_name, alias in imports:
        binding = alias or module_name
        for callable_name in asserted_callables:
            if not callable_name.startswith(f"{binding}."):
                continue
            function_name = callable_name.split(".", 1)[1]
            targets.append((module_name, function_name, callable_name))
    return targets


def _collect_repair_proposals(
    validation_result: ToolResult,
    workspace_root: Path,
) -> list[RepairProposal]:
    if validation_result.ok:
        return []
    hints = _extract_failure_hints(validation_result.output)
    proposals: list[RepairProposal] = []
    test_files = [
        workspace_root / hint
        for hint in hints
        if "test" in Path(hint).name and (workspace_root / hint).exists()
    ]
    for test_file in test_files:
        try:
            test_text = test_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        asserted_callables = _extract_asserted_callables(test_text)
        targets = _from_import_targets(test_text) + _module_import_targets(test_text)
        for module_name, function_name, callable_name in targets:
            if asserted_callables and callable_name not in asserted_callables:
                continue
            expected_op = _expected_operator(function_name)
            source_file = workspace_root / f"{module_name}.py"
            if not source_file.exists():
                continue
            try:
                source_text = source_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if expected_op is not None:
                match = re.search(
                    rf"def\s+{function_name}\s*\([^)]*\):\s*\n(?:[ \t]+.*\n)*?[ \t]+(return\s+([A-Za-z_][A-Za-z0-9_]*)\s*([+\-*/])\s*([A-Za-z_][A-Za-z0-9_]*))",
                    source_text,
                    flags=re.MULTILINE,
                )
                if match:
                    old_return = match.group(1)
                    left = match.group(2)
                    current_op = match.group(3)
                    right = match.group(4)
                    if current_op != expected_op:
                        new_return = f"return {left} {expected_op} {right}"
                        score, evidence = _score_proposal(
                            callable_name=callable_name,
                            module_name=module_name,
                            asserted_callables=asserted_callables,
                            test_file=test_file,
                            proposal_kind="operator",
                        )
                        proposal = RepairProposal(
                            file=str(source_file.relative_to(workspace_root)),
                            old_text=old_return,
                            new_text=new_return,
                            reason=(
                                f"Test imports `{function_name}` from `{module_name}.py` and the return operator "
                                f"`{current_op}` conflicts with the expected behavior implied by the function name."
                            ),
                            score=score,
                            evidence=evidence,
                        )
                        if proposal not in proposals:
                            proposals.append(proposal)

            expected_literal = _extract_expected_literal(test_text, callable_name)
            if expected_literal is None:
                continue
            literal_match = re.search(
                rf"def\s+{function_name}\s*\([^)]*\):\s*\n(?:[ \t]+.*\n)*?[ \t]+(return\s+([\"'][^\"']*[\"']|\d+(?:\.\d+)?|True|False|None))",
                source_text,
                flags=re.MULTILINE,
            )
            if literal_match:
                old_return = literal_match.group(1)
                current_literal = literal_match.group(2)
                if current_literal != expected_literal:
                    new_return = f"return {expected_literal}"
                    score, evidence = _score_proposal(
                        callable_name=callable_name,
                        module_name=module_name,
                        asserted_callables=asserted_callables,
                        test_file=test_file,
                        proposal_kind="literal",
                    )
                    proposal = RepairProposal(
                        file=str(source_file.relative_to(workspace_root)),
                        old_text=old_return,
                        new_text=new_return,
                        reason=(
                            f"Test expects `{function_name}()` to return `{expected_literal}`, "
                            f"but `{module_name}.py` returns `{current_literal}`."
                        ),
                        score=score,
                        evidence=evidence,
                    )
                    if proposal not in proposals:
                        proposals.append(proposal)

            variable_return_match = re.search(
                rf"def\s+{function_name}\s*\([^)]*\):\s*\n(?:[ \t]+.*\n)*?[ \t]+return\s+([A-Za-z_][A-Za-z0-9_]*)",
                source_text,
                flags=re.MULTILINE,
            )
            if not variable_return_match:
                continue
            variable_name = variable_return_match.group(1)
            assignment_match = re.search(
                rf"^({re.escape(variable_name)}\s*=\s*([\"'][^\"']*[\"']|\d+(?:\.\d+)?|True|False|None))$",
                source_text,
                flags=re.MULTILINE,
            )
            if not assignment_match:
                continue
            old_assignment = assignment_match.group(1)
            current_literal = assignment_match.group(2)
            if current_literal == expected_literal:
                continue
            new_assignment = f"{variable_name} = {expected_literal}"
            score, evidence = _score_proposal(
                callable_name=callable_name,
                module_name=module_name,
                asserted_callables=asserted_callables,
                test_file=test_file,
                proposal_kind="constant",
            )
            proposal = RepairProposal(
                file=str(source_file.relative_to(workspace_root)),
                old_text=old_assignment,
                new_text=new_assignment,
                reason=(
                    f"Test expects `{callable_name}()` to produce `{expected_literal}`, "
                    f"and `{module_name}.py` returns `{variable_name}` which is currently `{current_literal}`."
                ),
                score=score,
                evidence=evidence,
            )
            if proposal not in proposals:
                proposals.append(proposal)
    return proposals


def _select_repair_proposal(proposals: list[RepairProposal]) -> RepairProposal | None:
    if not proposals:
        return None
    proposals_sorted = sorted(
        proposals,
        key=lambda proposal: (
            -proposal.score,
            proposal.file.count("/"),
            len(proposal.old_text),
            proposal.file,
        ),
    )
    return proposals_sorted[0]


def _proposal_to_actions(
    proposal: RepairProposal,
    workspace_root: Path,
    *,
    validation_command: str,
) -> list[ToolRequest]:
    actions = [
        ToolRequest(
            name="edit_file",
            kind=ToolKind.FILE_EDIT,
            target=str(workspace_root / proposal.file),
            args={"old_text": proposal.old_text, "new_text": proposal.new_text},
        )
    ]
    if validation_command:
        actions.append(
            ToolRequest(
                name="run_command",
                kind=ToolKind.COMMAND,
                target=str(workspace_root),
                args={"command": validation_command, "timeout_seconds": "15", "max_chars": "4000"},
            )
        )
    return actions


def _run_action(
    record: SessionRecord,
    store: SessionStore,
    workspace_root: Path,
    action: ToolRequest,
    *,
    auto_approve_commands: bool,
    prior_record: SessionRecord | None = None,
    prior_handoff: HandoffArtifact | None = None,
) -> tuple[bool, ToolResult | None]:
    store.append_event(
        record,
        "tool_request",
        json.dumps(
            {
                "name": action.name,
                "kind": action.kind.value,
                "target": action.target,
                "args": action.args,
            },
            sort_keys=True,
        ),
    )
    permission = decide_permission(action, workspace_root)
    store.append_event(record, "permission", f"{action.name} -> {permission.value}")
    if permission is PermissionOutcome.DENY:
        record.status = SessionStatus.FAILED
        record.final_report = f"Tool request {action.name} was denied by workspace policy."
        _build_working_memory(record, None, prior_record, prior_handoff)
        record.validation_summary = summarize_validation(None)
        _save_procedural_repair_record(
            store,
            record,
            trigger_condition=f"tool `{action.name}` was denied by workspace policy",
            failure_pattern="permission_denied",
            recommended_recovery="Review the requested tool target and keep future actions inside the workspace boundary.",
        )
        _save_session_record(store, record)
        store.save_handoff(record, reason="permission_denied")
        return False, None
    if permission is PermissionOutcome.ASK and not auto_approve_commands:
        store.append_event(
            record,
            "approval_required",
            f"{action.name} requires approval before execution.",
        )
        record.status = SessionStatus.FAILED
        record.final_report = f"Stopped before running {action.name}; approval is required."
        _build_working_memory(record, None, prior_record, prior_handoff)
        record.validation_summary = summarize_validation(None)
        _save_procedural_repair_record(
            store,
            record,
            trigger_condition=f"tool `{action.name}` required approval",
            failure_pattern="approval_required",
            recommended_recovery="Request or provide approval before rerunning the command-dependent step.",
        )
        _save_session_record(store, record)
        store.save_handoff(record, reason="approval_required")
        return False, None
    if permission is PermissionOutcome.ASK and auto_approve_commands:
        store.append_event(
            record,
            "approval_auto_granted",
            f"{action.name} was auto-approved for this session.",
        )

    tool_result = execute_tool(action, workspace_root)
    store.append_event(record, "tool_result", f"{action.name}: {tool_result.output}")
    _record_action_evidence(record, workspace_root, action, tool_result)
    return True, tool_result


def _record_action_evidence(
    record: SessionRecord,
    workspace_root: Path,
    action: ToolRequest,
    tool_result: ToolResult,
) -> None:
    if action.name == "read_file":
        target_path = Path(action.target).resolve()
        if is_ignored_path(target_path, workspace_root):
            return
        rel = str(target_path.relative_to(workspace_root.resolve()))
        if rel not in record.inspected_files:
            record.inspected_files.append(rel)
    elif action.name == "search_code":
        for line in tool_result.output.splitlines():
            if ":" not in line:
                continue
            rel = line.split(":", 1)[0]
            rel_path = workspace_root / rel
            if rel and not is_ignored_path(rel_path, workspace_root) and rel not in record.inspected_files:
                record.inspected_files.append(rel)
    elif action.name == "edit_file":
        target_path = Path(action.target).resolve()
        if is_ignored_path(target_path, workspace_root):
            return
        rel = str(target_path.relative_to(workspace_root.resolve()))
        if rel not in record.changed_files:
            record.changed_files.append(rel)
    elif action.name == "rename_symbol_in_file":
        target_path = Path(action.target).resolve()
        if is_ignored_path(target_path, workspace_root):
            return
        rel = str(target_path.relative_to(workspace_root.resolve()))
        if rel not in record.changed_files:
            record.changed_files.append(rel)
        if rel not in record.inspected_files:
            record.inspected_files.append(rel)


def _append_rationale(record: SessionRecord, message: str) -> None:
    if message not in record.rationale:
        record.rationale.append(message)


def _build_working_memory(
    record: SessionRecord,
    validation_result: ToolResult | None,
    prior_record: SessionRecord | None,
    prior_handoff: HandoffArtifact | None = None,
    recalled_repairs: list[ProceduralRepairRecord] | None = None,
    prior_compact_context: CompactContextArtifact | None = None,
) -> None:
    focus: list[str] = []
    if record.proposed_changes:
        for proposal in record.proposed_changes[:2]:
            focus.append(f"change:{proposal.file}")
    elif record.candidate_proposals:
        for proposal in record.candidate_proposals[:2]:
            focus.append(f"candidate:{proposal.file}")
    else:
        for file_name in record.inspected_files[:2]:
            focus.append(f"inspect:{file_name}")
    for reason in record.rationale[-2:]:
        if reason not in focus:
            focus.append(reason)

    if validation_result is None:
        next_step = "Pick a validation or inspection step if the user continues this task."
    elif validation_result.ok:
        next_step = "Extend the task or review the verified changes if more work is needed."
    elif record.task_flow is TaskFlow.DIAGNOSE:
        next_step = "Choose whether to repair the failure or continue diagnosis on the reported hints."
    else:
        next_step = "Investigate the remaining failure hints before attempting another change."

    resume_context = ""
    if prior_record is not None:
        resume_context = f"from={prior_record.session_id}"
        if prior_record.working_memory.next_step:
            resume_context += f" prior_next={prior_record.working_memory.next_step}"
    elif prior_handoff is not None:
        resume_context = f"handoff={prior_handoff.session_id}"
        if prior_handoff.next_step:
            resume_context += f" prior_next={prior_handoff.next_step}"

    record.working_memory.task_flow = record.task_flow.value
    record.working_memory.resume_context = resume_context
    record.working_memory.focus = focus[:4]
    record.working_memory.inspected_files = record.inspected_files[:4]
    record.working_memory.changed_files = record.changed_files[:4]
    record.working_memory.last_validation = summarize_validation(validation_result)
    record.working_memory.next_step = next_step
    record.working_memory.belief = _build_belief_memory(record, validation_result)
    record.working_memory.progress = _build_progress_memory(record, validation_result, next_step)
    record.working_memory.experience = _build_experience_memory(
        record,
        prior_record,
        prior_handoff,
        recalled_repairs,
        prior_compact_context,
    )
    record.working_summary = summarize_working_memory(record.working_memory)


def _build_belief_memory(
    record: SessionRecord,
    validation_result: ToolResult | None,
) -> list[str]:
    belief = [
        f"task_flow={record.task_flow.value}",
        f"workspace={record.workspace_root}",
    ]
    if record.task_plan is not None and record.task_plan.affected_behavior_ids:
        belief.append(f"affected_behaviors={','.join(record.task_plan.affected_behavior_ids)}")
    if record.inspected_files:
        belief.append(f"inspected={','.join(record.inspected_files[:4])}")
    validation_summary = summarize_validation(validation_result)
    if validation_summary:
        belief.append(f"validation={validation_summary}")
    return belief[:6]


def _build_progress_memory(
    record: SessionRecord,
    validation_result: ToolResult | None,
    next_step: str,
) -> list[str]:
    progress: list[str] = []
    if record.task_plan is not None and record.task_plan.initial_actions:
        progress.append(f"initial_actions={','.join(record.task_plan.initial_actions)}")
    if record.changed_files:
        progress.append(f"changed={','.join(record.changed_files[:4])}")
    validation_summary = summarize_validation(validation_result)
    if validation_summary:
        progress.append(f"validation_state={validation_summary}")
    progress.append(f"next={next_step}")
    return progress[:6]


def _build_experience_memory(
    record: SessionRecord,
    prior_record: SessionRecord | None,
    prior_handoff: HandoffArtifact | None = None,
    recalled_repairs: list[ProceduralRepairRecord] | None = None,
    prior_compact_context: CompactContextArtifact | None = None,
) -> list[str]:
    experience: list[str] = []
    for repair in (recalled_repairs or [])[:2]:
        experience.append(f"recalled_repair={repair.repair_id}:{repair.failure_pattern}")
    if prior_compact_context is not None:
        experience.append(f"resumed_from_compact={prior_compact_context.session_id}")
        if prior_compact_context.experience:
            experience.extend(prior_compact_context.experience[:2])
    if prior_record is not None:
        experience.append(f"resumed_from={prior_record.session_id}")
        if prior_record.working_memory.experience:
            experience.extend(prior_record.working_memory.experience[:2])
    if prior_handoff is not None:
        experience.append(f"resumed_from_handoff={prior_handoff.session_id}")
        if prior_handoff.belief:
            experience.append(f"handoff_belief={prior_handoff.belief[0]}")
        if prior_handoff.progress:
            experience.append(f"handoff_progress={prior_handoff.progress[-1]}")
        if prior_handoff.experience:
            experience.extend(prior_handoff.experience[:2])
    if record.candidate_proposals:
        experience.append(f"candidate_repairs={len(record.candidate_proposals)}")
    if record.task_plan is not None:
        for reason in record.task_plan.reasons:
            if "module-aware" in reason or "fallback" in reason:
                experience.append(reason)
                break
    return experience[:6]


def _build_procedural_repair_record(
    record: SessionRecord,
    *,
    trigger_condition: str,
    failure_pattern: str,
    recommended_recovery: str,
) -> ProceduralRepairRecord:
    affected_behavior_ids: list[str] = []
    if record.task_plan is not None:
        affected_behavior_ids = list(record.task_plan.affected_behavior_ids)
    source_evidence = list(record.inspected_files[:4])
    if record.changed_files:
        source_evidence.extend(f"changed:{path}" for path in record.changed_files[:4])
    validation_evidence: list[str] = []
    if record.validation_summary:
        validation_evidence.append(record.validation_summary)
    if record.final_report:
        validation_evidence.append(record.final_report[:500])
    repair_id = f"{record.session_id}-{failure_pattern.replace('_', '-')}"
    return ProceduralRepairRecord(
        repair_id=repair_id,
        source_session_id=record.session_id,
        task_class=record.task_flow.value,
        trigger_condition=trigger_condition,
        failure_pattern=failure_pattern,
        recommended_recovery=recommended_recovery,
        source_evidence=source_evidence,
        validation_evidence=validation_evidence,
        affected_behavior_ids=affected_behavior_ids,
        support_count=1,
        status="candidate",
    )


def _save_procedural_repair_record(
    store: SessionStore,
    record: SessionRecord,
    *,
    trigger_condition: str,
    failure_pattern: str,
    recommended_recovery: str,
) -> ProceduralRepairRecord:
    repair = _build_procedural_repair_record(
        record,
        trigger_condition=trigger_condition,
        failure_pattern=failure_pattern,
        recommended_recovery=recommended_recovery,
    )
    store.save_procedural_repair_record(repair)
    store.append_event(record, "procedural_repair", f"candidate={repair.repair_id}")
    return repair


def _build_final_report(record: SessionRecord, validation_result: ToolResult | None) -> str:
    parts = [f"Task flow: {record.task_flow.value}.", summarize_validation(validation_result)]
    if record.resumed_from_session_id:
        parts.append(f"Resumed from session {record.resumed_from_session_id}.")
    if record.inspected_files:
        parts.append(f"Inspected: {', '.join(record.inspected_files)}.")
    if record.candidate_proposals:
        candidate_summaries = [
            f"{proposal.file} [score={proposal.score}] (`{proposal.old_text}` -> `{proposal.new_text}`)"
            for proposal in record.candidate_proposals
        ]
        parts.append(f"Candidates: {'; '.join(candidate_summaries)}.")
    if record.proposed_changes:
        proposal_summaries = [
            f"{proposal.file} [score={proposal.score}] (`{proposal.old_text}` -> `{proposal.new_text}`)"
            for proposal in record.proposed_changes
        ]
        parts.append(f"Proposed: {'; '.join(proposal_summaries)}.")
    if record.changed_files:
        parts.append(f"Changed: {', '.join(record.changed_files)}.")
    if record.rationale:
        parts.append(f"Why: {' '.join(record.rationale)}")
    return " ".join(parts)


def run_session(
    request: str,
    start_path: Path,
    store: SessionStore,
    *,
    auto_approve_commands: bool = False,
    resume_from_session_id: str | None = None,
    resume_from_handoff_id: str | None = None,
    planner_strategy: str | None = None,
) -> SessionRecord:
    workspace = build_workspace_summary(start_path)
    task_plan = build_task_plan(
        request,
        workspace.root,
        workspace.instruction_files,
        planner_strategy=planner_strategy,
    )
    task_flow = task_plan.task_flow
    prior_record: SessionRecord | None = None
    prior_handoff: HandoffArtifact | None = None
    prior_compact_context: CompactContextArtifact | None = None
    if resume_from_session_id is not None:
        prior_record = store.load(resume_from_session_id)
        prior_compact_context = store.maybe_load_compact_context(resume_from_session_id)
        _inherit_resume_validation_command(request, task_plan, prior_record)
    if resume_from_handoff_id is not None:
        prior_handoff = store.load_handoff(resume_from_handoff_id)
    accepted_repairs = store.list_procedural_repair_records(
        task_class=task_flow.value,
        status="accepted",
    )
    candidate_repairs = store.list_procedural_repair_records(
        task_class=task_flow.value,
        status="candidate",
    )
    recalled_repairs = (accepted_repairs + candidate_repairs)[:2]
    record = SessionRecord(
        session_id=uuid4().hex,
        request=request,
        workspace_root=workspace.root,
        task_flow=task_flow,
        task_plan=task_plan,
        resumed_from_session_id=resume_from_session_id or resume_from_handoff_id,
    )
    if prior_record is not None:
        if prior_compact_context is not None:
            record.inspected_files = list(prior_compact_context.inspected_files)
            record.changed_files = list(prior_compact_context.changed_files)
            record.working_memory = WorkingMemory(
                task_flow=prior_compact_context.task_flow,
                resume_context=f"compact={prior_compact_context.session_id}",
                focus=list(prior_compact_context.affected_behavior_ids[:4]),
                inspected_files=list(prior_compact_context.inspected_files[:4]),
                changed_files=list(prior_compact_context.changed_files[:4]),
                last_validation=prior_compact_context.validation_summary,
                next_step=prior_compact_context.next_step,
                belief=list(prior_compact_context.belief),
                progress=list(prior_compact_context.progress),
                experience=list(prior_compact_context.experience),
            )
            record.working_summary = prior_compact_context.summary or summarize_working_memory(record.working_memory)
        else:
            record.inspected_files = list(prior_record.inspected_files)
            record.changed_files = list(prior_record.changed_files)
            record.working_memory = WorkingMemory(
                task_flow=prior_record.working_memory.task_flow,
                resume_context=prior_record.working_memory.resume_context,
                focus=list(prior_record.working_memory.focus),
                inspected_files=list(prior_record.working_memory.inspected_files),
                changed_files=list(prior_record.working_memory.changed_files),
                last_validation=prior_record.working_memory.last_validation,
                next_step=prior_record.working_memory.next_step,
                belief=list(prior_record.working_memory.belief),
                progress=list(prior_record.working_memory.progress),
                experience=list(prior_record.working_memory.experience),
            )
            record.working_summary = prior_record.working_summary
        record.rationale = list(prior_record.rationale)
        store.append_event(
            record,
            "resume",
            f"resumed_from={prior_record.session_id} prior_status={prior_record.status.value}",
        )
        if prior_compact_context is not None:
            store.append_event(
                record,
                "compact_resume",
                f"resumed_from_compact={prior_compact_context.session_id}",
            )
        resume_source = (
            "its compact continuation state"
            if prior_compact_context is not None
            else "its inspected files, changed files, and working summary"
        )
        _append_rationale(
            record,
            f"Resumed from prior session `{prior_record.session_id}` after reviewing {resume_source}.",
        )
    elif prior_handoff is not None:
        record.inspected_files = list(prior_handoff.inspected_files)
        record.changed_files = list(prior_handoff.changed_files)
        record.working_memory = WorkingMemory(
            task_flow=prior_handoff.task_flow,
            resume_context=f"handoff={prior_handoff.session_id}",
            focus=list(prior_handoff.affected_behavior_ids[:4]),
            inspected_files=list(prior_handoff.inspected_files[:4]),
            changed_files=list(prior_handoff.changed_files[:4]),
            last_validation=prior_handoff.validation_summary,
            next_step=prior_handoff.next_step,
            belief=list(prior_handoff.belief),
            progress=list(prior_handoff.progress),
            experience=list(prior_handoff.experience),
        )
        record.working_summary = summarize_working_memory(record.working_memory)
        store.append_event(
            record,
            "handoff_resume",
            f"resumed_from_handoff={prior_handoff.session_id} reason={prior_handoff.reason}",
        )
        _append_rationale(
            record,
            (
                f"Resumed from handoff `{prior_handoff.session_id}` after reviewing "
                f"its blocker and BPE continuation state."
            ),
        )
    store.append_event(record, "request", request)
    store.append_event(record, "task_flow", task_flow.value)
    store.append_event(record, "task_plan", summarize_task_plan(task_plan))
    if recalled_repairs:
        store.append_event(
            record,
            "repair_memory",
            "recalled=" + ",".join(repair.repair_id for repair in recalled_repairs),
        )
    store.append_event(
        record,
        "workspace",
        f"root={workspace.root} branch={workspace.branch} instructions={workspace.instruction_files}",
    )
    actions = build_initial_actions(
        request,
        workspace.root,
        workspace.instruction_files,
        task_flow,
        feature_strategy=task_plan.feature_strategy,
        feature_arguments=task_plan.feature_arguments,
        validation_command=task_plan.validation_command,
    )
    store.append_event(record, "plan", f"planned_actions={','.join(action.name for action in actions)}")
    _append_rationale(
        record,
        f"Classified the request as the `{task_flow.value}` flow and planned validation with `{task_plan.validation_command or 'none'}`.",
    )
    validation_result: ToolResult | None = None
    rename_request = _extract_rename_request(request)

    for action in actions:
        ok, tool_result = _run_action(
            record,
            store,
            workspace.root,
            action,
            auto_approve_commands=auto_approve_commands,
            prior_record=prior_record,
            prior_handoff=prior_handoff,
        )
        if not ok:
            return record
        assert tool_result is not None
        if action.name == "run_command":
            validation_result = tool_result
            follow_up_actions = _build_follow_up_actions(validation_result, workspace.root)
            if follow_up_actions:
                store.append_event(
                    record,
                    "diagnosis",
                    f"derived_follow_up_actions={','.join(action.name for action in follow_up_actions)}",
                )
                _append_rationale(
                    record,
                    "Used failing test output to derive follow-up code search actions.",
                )
            for follow_up_action in follow_up_actions:
                ok, _ = _run_action(
                    record,
                    store,
                    workspace.root,
                    follow_up_action,
                    auto_approve_commands=auto_approve_commands,
                    prior_record=prior_record,
                    prior_handoff=prior_handoff,
                )
                if not ok:
                    return record
            if task_flow is TaskFlow.DIAGNOSE:
                _append_rationale(
                    record,
                    "Diagnose flow stopped after collecting failure evidence without applying edits.",
                )
                continue
            candidate_proposals = _collect_repair_proposals(validation_result, workspace.root)
            if candidate_proposals:
                record.candidate_proposals = candidate_proposals
                store.append_event(
                    record,
                    "repair_candidates",
                    f"count={len(candidate_proposals)}",
                )
                _append_rationale(
                    record,
                    f"Generated {len(candidate_proposals)} repair candidate(s) from failing test evidence.",
                )
            repair_proposal = _select_repair_proposal(candidate_proposals)
            repair_actions: list[ToolRequest] = []
            if repair_proposal is not None:
                record.proposed_changes.append(repair_proposal)
                store.append_event(
                    record,
                    "repair_plan",
                    (
                        "proposal="
                        f"{repair_proposal.file}: {repair_proposal.old_text} -> {repair_proposal.new_text}"
                        f" [score={repair_proposal.score}]"
                    ),
                )
                _append_rationale(
                    record,
                    repair_proposal.reason,
                )
                repair_actions = _proposal_to_actions(
                    repair_proposal,
                    workspace.root,
                    validation_command=task_plan.validation_command,
                )
            for repair_action in repair_actions:
                ok, repair_result = _run_action(
                    record,
                    store,
                    workspace.root,
                    repair_action,
                    auto_approve_commands=auto_approve_commands,
                    prior_record=prior_record,
                    prior_handoff=prior_handoff,
                )
                if not ok:
                    return record
                assert repair_result is not None
                if repair_action.name == "run_command":
                    validation_result = repair_result

    if task_flow is TaskFlow.RENAME and rename_request is not None:
        old_name, new_name = rename_request
        rename_candidates = _collect_symbol_rename_proposals(workspace.root, old_name, new_name)
        if rename_candidates:
            record.candidate_proposals = rename_candidates
            record.proposed_changes = list(rename_candidates)
            store.append_event(
                record,
                "rename_plan",
                f"rename={old_name}->{new_name} files={len(rename_candidates)}",
            )
            _append_rationale(
                record,
                f"Prepared a safe multi-file rename from `{old_name}` to `{new_name}` using exact symbol matches.",
            )
            rename_actions = _rename_proposals_to_actions(
                rename_candidates,
                workspace.root,
                validation_command=task_plan.validation_command,
            )
            for rename_action in rename_actions:
                ok, rename_result = _run_action(
                    record,
                    store,
                    workspace.root,
                    rename_action,
                    auto_approve_commands=auto_approve_commands,
                    prior_record=prior_record,
                    prior_handoff=prior_handoff,
                )
                if not ok:
                    return record
                assert rename_result is not None
                if rename_action.name == "run_command":
                    validation_result = rename_result
        else:
            _append_rationale(
                record,
                f"No exact symbol matches for `{old_name}` were found in the workspace.",
            )

    if task_flow is TaskFlow.FEATURE and task_plan.feature_strategy == "cli_flag":
        cli_flag_request = task_plan.feature_arguments["flag_name"]
        feature_candidates = _collect_cli_flag_proposals(workspace.root, cli_flag_request)
        if feature_candidates:
            record.candidate_proposals = feature_candidates
            record.proposed_changes = list(feature_candidates)
            store.append_event(
                record,
                "feature_plan",
                f"cli_flag={cli_flag_request} files={len(feature_candidates)}",
            )
            _append_rationale(
                record,
                f"Prepared a CLI flag feature edit for `{cli_flag_request}` in the detected argparse entrypoint.",
            )
            feature_actions = _feature_proposals_to_actions(
                feature_candidates,
                workspace.root,
                validation_command=task_plan.validation_command,
            )
            for feature_action in feature_actions:
                ok, feature_result = _run_action(
                    record,
                    store,
                    workspace.root,
                    feature_action,
                    auto_approve_commands=auto_approve_commands,
                    prior_record=prior_record,
                    prior_handoff=prior_handoff,
                )
                if not ok:
                    return record
                assert feature_result is not None
                if feature_action.name == "run_command":
                    validation_result = feature_result
        else:
            _append_rationale(
                record,
                f"No argparse parser without `{cli_flag_request}` was found in the workspace.",
            )

    if task_flow is TaskFlow.FEATURE and task_plan.feature_strategy == "config_option":
        option_name = task_plan.feature_arguments["option_name"]
        value_literal = task_plan.feature_arguments["value_literal"]
        feature_candidates = _collect_config_option_proposals(workspace.root, option_name, value_literal)
        if feature_candidates:
            record.candidate_proposals = feature_candidates
            record.proposed_changes = list(feature_candidates)
            store.append_event(
                record,
                "feature_plan",
                f"config_option={option_name} default={value_literal} files={len(feature_candidates)}",
            )
            _append_rationale(
                record,
                f"Prepared a config option feature edit for `{option_name}` with default `{value_literal}` in the detected config mapping.",
            )
            feature_actions = _feature_proposals_to_actions(
                feature_candidates,
                workspace.root,
                validation_command=task_plan.validation_command,
            )
            for feature_action in feature_actions:
                ok, feature_result = _run_action(
                    record,
                    store,
                    workspace.root,
                    feature_action,
                    auto_approve_commands=auto_approve_commands,
                    prior_record=prior_record,
                    prior_handoff=prior_handoff,
                )
                if not ok:
                    return record
                assert feature_result is not None
                if feature_action.name == "run_command":
                    validation_result = feature_result
        else:
            _append_rationale(
                record,
                f"No config-style mapping without `{option_name}` was found in the workspace.",
            )

    if task_flow is TaskFlow.FEATURE and task_plan.feature_strategy == "env_var":
        env_name = task_plan.feature_arguments["env_name"]
        option_name = task_plan.feature_arguments["option_name"]
        value_literal = task_plan.feature_arguments["value_literal"]
        feature_candidates = _collect_env_var_config_proposals(
            workspace.root,
            env_name,
            option_name,
            value_literal,
        )
        if feature_candidates:
            record.candidate_proposals = feature_candidates
            record.proposed_changes = list(feature_candidates)
            store.append_event(
                record,
                "feature_plan",
                f"env_var={env_name} option={option_name} default={value_literal} files={len(feature_candidates)}",
            )
            _append_rationale(
                record,
                f"Prepared an environment-variable config feature edit for `{env_name}` with default `{value_literal}` in the detected config mapping.",
            )
            feature_actions = _feature_proposals_to_actions(
                feature_candidates,
                workspace.root,
                validation_command=task_plan.validation_command,
            )
            for feature_action in feature_actions:
                ok, feature_result = _run_action(
                    record,
                    store,
                    workspace.root,
                    feature_action,
                    auto_approve_commands=auto_approve_commands,
                    prior_record=prior_record,
                    prior_handoff=prior_handoff,
                )
                if not ok:
                    return record
                assert feature_result is not None
                if feature_action.name == "run_command":
                    validation_result = feature_result
        else:
            _append_rationale(
                record,
                (
                    f"No config-style mapping with `os` support was found for the `{env_name}` "
                    f"environment-variable feature request."
                ),
            )

    _build_working_memory(
        record,
        validation_result,
        prior_record,
        prior_handoff,
        recalled_repairs,
        prior_compact_context,
    )
    record.validation_summary = summarize_validation(validation_result)
    record.final_report = _build_final_report(record, validation_result)
    if validation_result is not None and not validation_result.ok:
        hints = _extract_failure_hints(validation_result.output)
        if hints:
            record.final_report += f" Failure hints: {', '.join(hints)}."
    if validation_result is not None and not validation_result.ok:
        record.status = SessionStatus.FAILED
    else:
        record.status = SessionStatus.COMPLETED
    _save_session_record(store, record)
    if record.status is SessionStatus.FAILED:
        _save_procedural_repair_record(
            store,
            record,
            trigger_condition="validation command completed with a failing result",
            failure_pattern="validation_failed",
            recommended_recovery="Inspect validation output, preserve the selected validation command, and continue from the recorded failure hints.",
        )
        _save_session_record(store, record)
        store.save_handoff(record, reason="validation_failed")
    return record


def _save_session_record(store: SessionStore, record: SessionRecord) -> None:
    store.save(record)
    store.save_compact_context(record)


def _inherit_resume_validation_command(
    request: str,
    task_plan: TaskPlan,
    prior_record: SessionRecord,
) -> None:
    lowered = request.lower()
    if "continue" not in lowered and "pick up" not in lowered:
        return
    if "rerun" not in lowered and "test" not in lowered:
        return
    prior_validation = prior_record.task_plan.validation_command if prior_record.task_plan is not None else ""
    if not prior_validation or prior_validation == "pytest -q":
        return
    if task_plan.validation_command == prior_validation:
        return
    task_plan.validation_command = prior_validation
    reason = f"selected validation command `{prior_validation}` from resumed session validation context"
    if reason not in task_plan.reasons:
        task_plan.reasons.append(reason)
