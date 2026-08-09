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


@dataclass(slots=True)
class TaskPlan:
    task_flow: TaskFlow
    feature_strategy: str = ""
    feature_arguments: dict[str, str] = field(default_factory=dict)
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
