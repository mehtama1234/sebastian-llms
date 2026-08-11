from pathlib import Path

from coding_agent_v1.behavior_index import (
    get_behavior_entry,
    infer_behavior_lookup,
    list_behavior_entries,
    validate_behavior_entry,
)
from coding_agent_v1.models import TaskFlow


def _write_minimal_harness_workspace(root: Path) -> None:
    package = root / "src" / "coding_agent_v1"
    package.mkdir(parents=True)
    (package / "agent_loop.py").write_text(
        "def classify_task_flow(): pass\n"
        "def _select_task_flow(): pass\n"
        "def build_task_plan(): pass\n"
        "def build_initial_actions(): pass\n"
        "def _choose_validation_command(): pass\n"
        "def _validation_reason(): pass\n"
        "def run_session(): pass\n"
        "resumed_from_session_id = None\n"
        "resume_context = ''\n",
        encoding="utf-8",
    )
    (package / "planner.py").write_text(
        "def select_task_flow_from_candidates(): pass\n"
        "def find_python_test_paths(): pass\n",
        encoding="utf-8",
    )
    (package / "models.py").write_text(
        "class TaskPlan: pass\n"
        "class WorkingMemory: pass\n"
        "class TaskFlow: pass\n"
        "class TaskFlowCandidate: pass\n"
        "class PermissionOutcome: pass\n"
        "class ToolKind: pass\n"
        "class ToolRequest: pass\n"
        "class ToolResult: pass\n"
        "class SessionRecord: pass\n"
        "class RepairProposal: pass\n"
        "candidate_proposals = []\n",
        encoding="utf-8",
    )
    (package / "session_store.py").write_text(
        "class SessionStore: pass\n"
        "def summarize_task_plan(): pass\n"
        "def summarize_working_memory(): pass\n"
        "candidate_proposals = []\n",
        encoding="utf-8",
    )
    (package / "permissions.py").write_text(
        "def decide_permission(): pass\n"
        "class PermissionOutcome: pass\n"
        "class ToolRequest: pass\n",
        encoding="utf-8",
    )
    (package / "tools.py").write_text(
        "def execute_tool(): pass\n"
        "def is_ignored_path(): pass\n"
        "class ToolResult: pass\n",
        encoding="utf-8",
    )
    (package / "eval_harness.py").write_text(
        "def run_eval_suite(): pass\n"
        "def compare_eval_summaries(): pass\n"
        "def audit_eval_baselines(): pass\n"
        "def build_eval_decision_artifact_index(): pass\n"
        "def resolve_decision_artifact_reference(): pass\n"
        "class EvalScenario: pass\n"
        "class EvalSummary: pass\n"
        "class EvalResult: pass\n"
        "class EvalComparisonSummary: pass\n"
        "class EvalComparisonResult: pass\n"
        "class EvalBaselineConfig: pass\n"
        "class EvalPromotionDecision: pass\n"
        "class EvalBaselineAuditSummary: pass\n"
        "class EvalDecisionArtifactIndex: pass\n",
        encoding="utf-8",
    )
    (package / "eval_catalog.py").write_text(
        "def load_eval_scenario_pack(): pass\n",
        encoding="utf-8",
    )
    (package / "cli.py").write_text(
        "def main(): pass\n"
        "def build_parser(): pass\n",
        encoding="utf-8",
    )


def test_behavior_index_lists_core_harness_behaviors() -> None:
    behavior_ids = {entry.behavior_id for entry in list_behavior_entries()}

    assert "task_planning" in behavior_ids
    assert "validation_selection" in behavior_ids
    assert "permission_decisions" in behavior_ids
    assert "handoff_and_resume" in behavior_ids
    assert "baseline_promotion" in behavior_ids
    assert "failure_memory" in behavior_ids


def test_behavior_entry_validation_detects_current_source_anchors(tmp_path: Path) -> None:
    _write_minimal_harness_workspace(tmp_path)
    entry = get_behavior_entry("validation_selection")

    assert entry is not None
    assert validate_behavior_entry(tmp_path, entry)


def test_behavior_entry_validation_detects_stale_source_anchors(tmp_path: Path) -> None:
    _write_minimal_harness_workspace(tmp_path)
    (tmp_path / "src" / "coding_agent_v1" / "agent_loop.py").write_text(
        "def unrelated(): pass\n",
        encoding="utf-8",
    )
    entry = get_behavior_entry("validation_selection")

    assert entry is not None
    assert not validate_behavior_entry(tmp_path, entry)


def test_infer_behavior_lookup_maps_validation_request_to_surfaces(tmp_path: Path) -> None:
    _write_minimal_harness_workspace(tmp_path)

    lookup = infer_behavior_lookup(
        "improve validation selection for rename tasks",
        tmp_path,
        TaskFlow.RENAME,
        validation_command="pytest -q tests/test_agent_loop.py",
    )

    assert lookup.behavior_ids == ["task_planning", "validation_selection"]
    assert "src/coding_agent_v1/agent_loop.py" in lookup.source_files
    assert "src/coding_agent_v1/planner.py" in lookup.source_files
    assert lookup.stale_behavior_ids == []


def test_infer_behavior_lookup_maps_nested_monorepo_harness_surfaces(tmp_path: Path) -> None:
    project_root = tmp_path / "projects" / "coding-agent-v1"
    _write_minimal_harness_workspace(project_root)

    lookup = infer_behavior_lookup(
        "improve validation selection for rename tasks",
        tmp_path,
        TaskFlow.RENAME,
        validation_command="pytest -q tests/test_agent_loop.py",
    )

    assert lookup.behavior_ids == ["task_planning", "validation_selection"]
    assert "projects/coding-agent-v1/src/coding_agent_v1/agent_loop.py" in lookup.source_files
    assert "projects/coding-agent-v1/src/coding_agent_v1/planner.py" in lookup.source_files
    assert lookup.stale_behavior_ids == []


def test_infer_behavior_lookup_maps_decision_artifact_review_request(tmp_path: Path) -> None:
    _write_minimal_harness_workspace(tmp_path)

    lookup = infer_behavior_lookup(
        "review the latest-promotion decision artifact and audit the baseline flow",
        tmp_path,
        TaskFlow.INSPECT,
    )

    assert "baseline_promotion" in lookup.behavior_ids
    assert "src/coding_agent_v1/eval_harness.py" in lookup.source_files
    assert "src/coding_agent_v1/cli.py" in lookup.source_files
    assert lookup.stale_behavior_ids == []


def test_infer_behavior_lookup_is_empty_outside_harness_workspace(tmp_path: Path) -> None:
    lookup = infer_behavior_lookup("fix the failing test", tmp_path, TaskFlow.FIX)

    assert lookup.behavior_ids == []
    assert lookup.source_files == []
