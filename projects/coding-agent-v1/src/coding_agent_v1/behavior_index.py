from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .models import TaskFlow


@dataclass(frozen=True, slots=True)
class BehaviorEntry:
    behavior_id: str
    description: str
    source_files: tuple[str, ...]
    symbols: tuple[str, ...] = ()
    related_state: tuple[str, ...] = ()
    related_tests: tuple[str, ...] = ()


@dataclass(slots=True)
class BehaviorLookupResult:
    behavior_ids: list[str]
    source_files: list[str]
    stale_behavior_ids: list[str] = field(default_factory=list)


CORE_BEHAVIORS: tuple[BehaviorEntry, ...] = (
    BehaviorEntry(
        behavior_id="task_classification",
        description="Classify user requests into inspect, fix, feature, rename, or diagnose task flows.",
        source_files=("src/coding_agent_v1/agent_loop.py", "src/coding_agent_v1/planner.py"),
        symbols=("classify_task_flow", "_select_task_flow", "select_task_flow_from_candidates"),
        related_state=("TaskFlow", "TaskFlowCandidate", "TaskPlan"),
        related_tests=("tests/test_agent_loop.py",),
    ),
    BehaviorEntry(
        behavior_id="task_planning",
        description="Build structured task plans with actions, validation commands, and planning rationale.",
        source_files=("src/coding_agent_v1/agent_loop.py", "src/coding_agent_v1/models.py"),
        symbols=("build_task_plan", "build_initial_actions", "TaskPlan"),
        related_state=("TaskPlan", "WorkingMemory"),
        related_tests=("tests/test_agent_loop.py",),
    ),
    BehaviorEntry(
        behavior_id="validation_selection",
        description="Choose targeted or broad validation commands from request and workspace evidence.",
        source_files=("src/coding_agent_v1/agent_loop.py", "src/coding_agent_v1/planner.py"),
        symbols=("_choose_validation_command", "_validation_reason", "find_python_test_paths"),
        related_state=("TaskPlan.validation_command", "SessionRecord.validation_summary"),
        related_tests=("tests/test_agent_loop.py", "tests/test_eval_harness.py"),
    ),
    BehaviorEntry(
        behavior_id="permission_decisions",
        description="Decide whether a tool request is allowed, denied, or requires approval.",
        source_files=("src/coding_agent_v1/permissions.py", "src/coding_agent_v1/tools.py"),
        symbols=("decide_permission", "PermissionOutcome", "ToolRequest"),
        related_state=("PermissionOutcome", "ToolKind"),
        related_tests=("tests/test_permissions.py", "tests/test_tools.py"),
    ),
    BehaviorEntry(
        behavior_id="tool_execution",
        description="Execute read, search, edit, and command tools under workspace and output limits.",
        source_files=("src/coding_agent_v1/tools.py",),
        symbols=("execute_tool", "is_ignored_path", "ToolResult"),
        related_state=("ToolRequest", "ToolResult"),
        related_tests=("tests/test_tools.py",),
    ),
    BehaviorEntry(
        behavior_id="session_persistence",
        description="Persist and reload session records, events, task plans, summaries, and outcomes.",
        source_files=("src/coding_agent_v1/session_store.py", "src/coding_agent_v1/models.py"),
        symbols=("SessionStore", "SessionRecord", "summarize_task_plan", "summarize_working_memory"),
        related_state=("SessionRecord", "WorkingMemory", "TaskPlan"),
        related_tests=("tests/test_session_store.py",),
    ),
    BehaviorEntry(
        behavior_id="handoff_and_resume",
        description="Resume work from prior session state and prepare for future handoff artifacts.",
        source_files=("src/coding_agent_v1/agent_loop.py", "src/coding_agent_v1/session_store.py"),
        symbols=("run_session", "resumed_from_session_id", "resume_context"),
        related_state=("SessionRecord.resumed_from_session_id", "WorkingMemory.resume_context"),
        related_tests=("tests/test_agent_loop.py", "tests/test_session_store.py"),
    ),
    BehaviorEntry(
        behavior_id="eval_execution",
        description="Run built-in and external eval scenarios and save eval summaries.",
        source_files=("src/coding_agent_v1/eval_harness.py", "src/coding_agent_v1/eval_catalog.py"),
        symbols=("run_eval_suite", "EvalScenario", "EvalSummary", "load_eval_scenario_pack"),
        related_state=("EvalScenario", "EvalResult", "EvalSummary"),
        related_tests=("tests/test_eval_harness.py", "tests/test_eval_catalog.py"),
    ),
    BehaviorEntry(
        behavior_id="eval_comparison",
        description="Compare eval artifacts and classify regressions, improvements, and unchanged scenarios.",
        source_files=("src/coding_agent_v1/eval_harness.py",),
        symbols=("compare_eval_summaries", "EvalComparisonSummary", "EvalComparisonResult"),
        related_state=("EvalComparisonSummary", "EvalComparisonResult"),
        related_tests=("tests/test_eval_harness.py", "tests/test_cli.py"),
    ),
    BehaviorEntry(
        behavior_id="baseline_promotion",
        description="Promote, audit, repair, and compare named eval baselines, and manage saved decision artifacts.",
        source_files=("src/coding_agent_v1/eval_harness.py", "src/coding_agent_v1/cli.py"),
        symbols=(
            "EvalBaselineConfig",
            "EvalPromotionDecision",
            "build_eval_decision_artifact_index",
            "resolve_decision_artifact_reference",
        ),
        related_state=(
            "EvalBaselineConfig",
            "EvalPromotionDecision",
            "EvalBaselineAuditSummary",
            "EvalDecisionArtifactIndex",
        ),
        related_tests=("tests/test_eval_harness.py", "tests/test_cli.py"),
    ),
    BehaviorEntry(
        behavior_id="failure_memory",
        description="Track planner, validation, and resume misses as future procedural repair evidence.",
        source_files=("src/coding_agent_v1/models.py", "src/coding_agent_v1/session_store.py"),
        symbols=("RepairProposal", "SessionRecord", "candidate_proposals"),
        related_state=("RepairProposal", "SessionRecord.candidate_proposals"),
        related_tests=("tests/test_agent_loop.py", "tests/test_session_store.py"),
    ),
)


def list_behavior_entries() -> list[BehaviorEntry]:
    return list(CORE_BEHAVIORS)


def get_behavior_entry(behavior_id: str) -> BehaviorEntry | None:
    for entry in CORE_BEHAVIORS:
        if entry.behavior_id == behavior_id:
            return entry
    return None


def has_behavior_index_workspace(workspace_root: Path) -> bool:
    return _behavior_source_prefix(workspace_root) is not None


def validate_behavior_entry(workspace_root: Path, entry: BehaviorEntry) -> bool:
    for source_file in entry.source_files:
        path = _resolve_behavior_source_file(workspace_root, source_file)
        if path is None:
            return False
        if not path.exists():
            return False
    for symbol in entry.symbols:
        if not any(
            _source_contains_symbol(path, symbol)
            for source_file in entry.source_files
            if (path := _resolve_behavior_source_file(workspace_root, source_file)) is not None
        ):
            return False
    return True


def infer_behavior_lookup(
    request: str,
    workspace_root: Path,
    task_flow: TaskFlow,
    *,
    feature_strategy: str = "",
    validation_command: str = "",
) -> BehaviorLookupResult:
    if not has_behavior_index_workspace(workspace_root):
        return BehaviorLookupResult(behavior_ids=[], source_files=[])

    lowered = request.lower()
    behavior_ids: list[str] = ["task_planning"]

    if any(term in lowered for term in ("classify", "classification", "task flow", "route request")):
        behavior_ids.append("task_classification")
    if validation_command or any(term in lowered for term in ("validation", "pytest", "test selection", "targeted test")):
        behavior_ids.append("validation_selection")
    if any(term in lowered for term in ("permission", "approval", "deny", "destructive", "safe command")):
        behavior_ids.append("permission_decisions")
    if any(term in lowered for term in ("tool", "command", "read file", "search", "edit")):
        behavior_ids.append("tool_execution")
    if any(term in lowered for term in ("session", "persist", "artifact", "summary", "review")):
        behavior_ids.append("session_persistence")
    if any(term in lowered for term in ("resume", "handoff", "interrupted", "continue")):
        behavior_ids.append("handoff_and_resume")
    if any(term in lowered for term in ("eval", "benchmark", "scenario", "regression")):
        behavior_ids.append("eval_execution")
    if any(term in lowered for term in ("compare", "comparison", "regression", "improvement")):
        behavior_ids.append("eval_comparison")
    if any(
        term in lowered
        for term in (
            "baseline",
            "promote",
            "promotion",
            "audit",
            "decision artifact",
            "latest-comparison",
            "latest-promotion",
            "prune decision",
        )
    ):
        behavior_ids.append("baseline_promotion")
    if any(term in lowered for term in ("failure", "miss", "repair", "lesson", "memory", "experience")):
        behavior_ids.append("failure_memory")

    if task_flow in {TaskFlow.FIX, TaskFlow.FEATURE, TaskFlow.RENAME}:
        behavior_ids.append("validation_selection")
    if task_flow is TaskFlow.DIAGNOSE:
        behavior_ids.append("session_persistence")
    if feature_strategy:
        behavior_ids.append("task_classification")

    deduped = _dedupe(behavior_ids)
    source_files = _dedupe(
        _display_behavior_source_file(workspace_root, source_file)
        for behavior_id in deduped
        for source_file in (get_behavior_entry(behavior_id).source_files if get_behavior_entry(behavior_id) else ())
    )
    stale_behavior_ids = [
        behavior_id
        for behavior_id in deduped
        if (entry := get_behavior_entry(behavior_id)) is not None
        and not validate_behavior_entry(workspace_root, entry)
    ]
    return BehaviorLookupResult(
        behavior_ids=deduped,
        source_files=source_files,
        stale_behavior_ids=stale_behavior_ids,
    )


def _source_contains_symbol(path: Path, symbol: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return symbol in text


def _behavior_source_prefix(workspace_root: Path) -> Path | None:
    if (workspace_root / "src" / "coding_agent_v1").is_dir():
        return Path(".")
    nested = workspace_root / "projects" / "coding-agent-v1"
    if (nested / "src" / "coding_agent_v1").is_dir():
        return Path("projects") / "coding-agent-v1"
    return None


def _resolve_behavior_source_file(workspace_root: Path, source_file: str) -> Path | None:
    prefix = _behavior_source_prefix(workspace_root)
    if prefix is None:
        return None
    return workspace_root / prefix / source_file


def _display_behavior_source_file(workspace_root: Path, source_file: str) -> str:
    prefix = _behavior_source_prefix(workspace_root)
    if prefix is None or str(prefix) == ".":
        return source_file
    return str(prefix / source_file)


def _dedupe(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
