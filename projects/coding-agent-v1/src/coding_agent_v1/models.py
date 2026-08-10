from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ToolKind(str, Enum):
    READ_ONLY = "read_only"
    FILE_EDIT = "file_edit"
    COMMAND = "command"
    APPROVAL = "approval"


class PermissionOutcome(str, Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


class SessionStatus(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskFlow(str, Enum):
    INSPECT = "inspect"
    FIX = "fix"
    FEATURE = "feature"
    RENAME = "rename"
    DIAGNOSE = "diagnose"


@dataclass(slots=True)
class ToolRequest:
    name: str
    kind: ToolKind
    target: str
    args: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ToolResult:
    name: str
    ok: bool
    output: str


@dataclass(slots=True)
class WorkspaceSummary:
    root: Path
    branch: str | None
    git_status: str | None
    top_level_entries: list[str]
    instruction_files: list[str]


@dataclass(slots=True)
class SessionEvent:
    kind: str
    message: str
    created_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class RepairProposal:
    file: str
    old_text: str
    new_text: str
    reason: str
    score: int = 0
    evidence: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorkingMemory:
    task_flow: str = ""
    resume_context: str = ""
    focus: list[str] = field(default_factory=list)
    inspected_files: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    last_validation: str = ""
    next_step: str = ""
    belief: list[str] = field(default_factory=list)
    progress: list[str] = field(default_factory=list)
    experience: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TaskPlan:
    task_flow: TaskFlow
    planner_strategy: str = "deterministic_heuristic"
    planner_strategy_reason: str = ""
    feature_strategy: str = ""
    feature_arguments: dict[str, str] = field(default_factory=dict)
    affected_behavior_ids: list[str] = field(default_factory=list)
    implementation_surfaces: list[str] = field(default_factory=list)
    initial_actions: list[str] = field(default_factory=list)
    validation_command: str = ""
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TaskFlowCandidate:
    task_flow: TaskFlow
    score: int
    priority: int
    reason: str


@dataclass(slots=True)
class SessionRecord:
    session_id: str
    request: str
    workspace_root: Path
    task_flow: TaskFlow = TaskFlow.INSPECT
    task_plan: TaskPlan | None = None
    resumed_from_session_id: str | None = None
    status: SessionStatus = SessionStatus.STARTED
    events: list[SessionEvent] = field(default_factory=list)
    inspected_files: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    candidate_proposals: list[RepairProposal] = field(default_factory=list)
    proposed_changes: list[RepairProposal] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    working_memory: WorkingMemory = field(default_factory=WorkingMemory)
    working_summary: str = ""
    validation_summary: str = ""
    final_report: str = ""


@dataclass(slots=True)
class HandoffArtifact:
    session_id: str
    request: str
    workspace_root: str
    status: str
    reason: str
    task_flow: str
    affected_behavior_ids: list[str] = field(default_factory=list)
    belief: list[str] = field(default_factory=list)
    progress: list[str] = field(default_factory=list)
    experience: list[str] = field(default_factory=list)
    inspected_files: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    validation_summary: str = ""
    blocker: str = ""
    next_step: str = ""


@dataclass(slots=True)
class CompactContextArtifact:
    session_id: str
    request: str
    workspace_root: str
    status: str
    task_flow: str
    compaction_trigger: str = "checkpoint"
    source_event_count: int = 0
    source_context_chars: int = 0
    affected_behavior_ids: list[str] = field(default_factory=list)
    implementation_surfaces: list[str] = field(default_factory=list)
    belief: list[str] = field(default_factory=list)
    progress: list[str] = field(default_factory=list)
    experience: list[str] = field(default_factory=list)
    inspected_files: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    validation_summary: str = ""
    blocker: str = ""
    next_step: str = ""
    summary: str = ""


@dataclass(slots=True)
class CompactContextIndexEntry:
    artifact_path: Path
    session_id: str
    status: str
    task_flow: str
    compaction_trigger: str
    source_event_count: int
    source_context_chars: int
    modified_at: float


@dataclass(slots=True)
class CompactContextPruneEntry:
    artifact_path: Path
    session_id: str
    compaction_trigger: str
    modified_at: float
    action: str
    reason: str


@dataclass(slots=True)
class CompactContextPruneSummary:
    base_dir: Path
    keep_newest: int
    include_size_triggered: bool
    kept_count: int
    prunable_count: int
    entries: list[CompactContextPruneEntry] = field(default_factory=list)


@dataclass(slots=True)
class ProceduralRepairRecord:
    repair_id: str
    source_session_id: str
    task_class: str
    trigger_condition: str
    failure_pattern: str
    recommended_recovery: str
    source_evidence: list[str] = field(default_factory=list)
    validation_evidence: list[str] = field(default_factory=list)
    affected_behavior_ids: list[str] = field(default_factory=list)
    support_count: int = 1
    status: str = "candidate"


@dataclass(slots=True)
class ProceduralRepairStatusAudit:
    audit_id: str
    repair_id: str
    previous_status: str
    new_status: str
    actor: str = "cli"
    reason: str = ""
    created_at: datetime = field(default_factory=utc_now)
