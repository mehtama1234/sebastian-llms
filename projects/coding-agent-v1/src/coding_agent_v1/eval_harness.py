from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import time
from uuid import uuid4

from .eval_catalog import list_executable_eval_scenarios, load_eval_scenario_pack
from .agent_loop import run_session
from .models import SessionRecord
from .session_store import SessionStore


@dataclass(slots=True)
class EvalScenario:
    name: str
    request: str
    setup_kind: str
    auto_approve_commands: bool = True
    task_class: str = "unknown"
    severity: str = "core"
    failure_modes: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(slots=True)
class EvalResult:
    scenario_name: str
    passed: bool
    session_id: str
    status: str
    final_report: str
    outcome_reason: str
    duration_seconds: float
    task_class: str = "unknown"
    severity: str = "core"
    failure_modes: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(slots=True)
class EvalSummary:
    total: int
    passed: int
    failed: int
    results: list[EvalResult]
    created_at: str
    run_label: str | None = None
    artifact_path: Path | None = None
    scenario_pack_id: str | None = None


@dataclass(slots=True)
class EvalComparisonResult:
    scenario_name: str
    task_class: str
    baseline_passed: bool
    candidate_passed: bool
    classification: str
    duration_delta_seconds: float
    baseline_reason: str
    candidate_reason: str
    failure_modes: tuple[str, ...] = ()


@dataclass(slots=True)
class EvalComparisonSummary:
    baseline_artifact_path: Path | None
    candidate_artifact_path: Path | None
    regressions: int
    improvements: int
    unchanged: int
    results: list[EvalComparisonResult]
    created_at: str
    artifact_path: Path | None = None


@dataclass(slots=True)
class EvalPromotionDecision:
    baseline_name: str
    candidate_reference: str
    promoted: bool
    comparison: EvalComparisonSummary
    artifact_path: Path | None = None
    config_path: Path | None = None
    created_at: str = ""
    decision_artifact_path: Path | None = None


@dataclass(slots=True)
class EvalHistoryEntry:
    artifact_path: Path | None
    created_at: str | None
    run_label: str | None
    passed: bool
    duration_seconds: float
    outcome_reason: str


@dataclass(slots=True)
class EvalScenarioTrend:
    scenario_name: str
    runs: int
    pass_count: int
    fail_count: int
    latest_passed: bool
    latest_duration_seconds: float
    average_duration_seconds: float
    trend: str
    history: list[EvalHistoryEntry]


@dataclass(slots=True)
class EvalHistorySummary:
    artifact_paths: list[Path]
    scenario_trends: list[EvalScenarioTrend]


@dataclass(slots=True)
class EvalArtifactIndexEntry:
    artifact_path: Path
    created_at: str
    run_label: str | None
    passed: int
    total: int
    pass_rate: float


@dataclass(slots=True)
class EvalArtifactIndex:
    artifact_dir: Path
    entries: list[EvalArtifactIndexEntry]


@dataclass(slots=True)
class EvalBaselineConfig:
    artifact_dir: Path
    baselines: dict[str, Path]


@dataclass(slots=True)
class EvalTaskClassSummaryEntry:
    task_class: str
    total: int
    passed: int
    failed: int
    scenario_names: tuple[str, ...]


@dataclass(slots=True)
class EvalFailureModeSummaryEntry:
    failure_mode: str
    scenario_count: int
    passed: int
    failed: int
    scenario_names: tuple[str, ...]


@dataclass(slots=True)
class EvalTaskClassComparisonEntry:
    task_class: str
    regressions: int
    improvements: int
    unchanged: int
    scenario_names: tuple[str, ...]


SCENARIOS = [
    EvalScenario(
        name="failing_test_repair",
        request="fix the failing test",
        setup_kind="repair",
        task_class="fix",
        severity="smoke",
        failure_modes=("no_op", "bad_validation_scope", "wrong_file_touched"),
        tags=("pytest", "repair", "single-module"),
    ),
    EvalScenario(
        name="natural_language_test_repair",
        request="make the failing tests pass",
        setup_kind="repair",
        task_class="fix",
        severity="core",
        failure_modes=("no_op", "partial_fix", "bad_validation_scope"),
        tags=("pytest", "natural-language", "repair"),
    ),
    EvalScenario(
        name="safe_multi_file_rename",
        request="rename add to plus",
        setup_kind="rename",
        task_class="rename",
        severity="smoke",
        failure_modes=("wrong_file_touched", "partial_fix", "regression_introduced"),
        tags=("rename", "symbol", "multi-file"),
    ),
    EvalScenario(
        name="cli_flag_feature",
        request="add a --verbose flag",
        setup_kind="cli_flag",
        task_class="feature",
        severity="smoke",
        failure_modes=("no_op", "partial_fix", "bad_validation_scope"),
        tags=("cli", "argparse", "feature"),
    ),
    EvalScenario(
        name="natural_language_cli_flag_feature",
        request="make the parser support verbose mode",
        setup_kind="cli_flag",
        task_class="feature",
        severity="core",
        failure_modes=("no_op", "partial_fix", "wrong_file_touched"),
        tags=("natural-language", "cli", "feature"),
    ),
    EvalScenario(
        name="module_aware_cli_feature",
        request="add a --verbose flag",
        setup_kind="module_aware_cli_flag",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "bad_validation_scope", "wrong_file_touched"),
        tags=("cli", "module-aware", "feature"),
    ),
    EvalScenario(
        name="single_test_workspace_fallback_cli_feature",
        request="add a --verbose flag",
        setup_kind="single_test_cli_flag",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "bad_validation_scope", "wrong_file_touched"),
        tags=("cli", "single-test", "feature"),
    ),
    EvalScenario(
        name="explicit_multi_test_cli_flag_feature",
        request=(
            "add a --verbose flag so "
            "[first](tests/regression/test_targeted_cli.py) and "
            "[second](tests/smoke/test_cli_smoke.py) pass"
        ),
        setup_kind="explicit_multi_test_cli_flag",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "bad_validation_scope", "wrong_file_touched"),
        tags=("cli", "multi-test", "feature"),
    ),
    EvalScenario(
        name="config_option_feature",
        request="add a timeout config option with default 30",
        setup_kind="config_option",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "bad_validation_scope", "wrong_file_touched"),
        tags=("config", "defaults", "feature"),
    ),
    EvalScenario(
        name="natural_language_config_option_feature",
        request="make config support timeout with default 30",
        setup_kind="config_option",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "bad_validation_scope", "wrong_file_touched"),
        tags=("config", "natural-language", "feature"),
    ),
    EvalScenario(
        name="env_var_feature",
        request="add APP_PROFILE environment variable with default advanced",
        setup_kind="env_var",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "regression_introduced", "bad_validation_scope"),
        tags=("env-var", "config", "feature"),
    ),
    EvalScenario(
        name="natural_language_env_var_feature",
        request="make config read profile from APP_PROFILE with default advanced",
        setup_kind="env_var",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "regression_introduced", "bad_validation_scope"),
        tags=("env-var", "natural-language", "feature"),
    ),
    EvalScenario(
        name="approval_required_boundary",
        request="run the tests",
        setup_kind="approval_boundary",
        auto_approve_commands=False,
        task_class="diagnose",
        severity="core",
        failure_modes=("unsafe_action", "no_op", "bad_validation_scope"),
        tags=("approval", "boundary", "diagnose"),
    ),
    EvalScenario(
        name="natural_language_diagnose_flow",
        request="investigate the failing tests",
        setup_kind="diagnose",
        task_class="diagnose",
        severity="smoke",
        failure_modes=("diagnose_edited_repo", "no_op", "bad_validation_scope"),
        tags=("diagnose", "natural-language", "no-edit"),
    ),
    EvalScenario(
        name="mixed_format_multi_test_diagnose_flow",
        request="'tests/quoted/test_first.py' and [second](tests/linked/test_second.py) are failing",
        setup_kind="diagnose_multi_test",
        task_class="diagnose",
        severity="core",
        failure_modes=("diagnose_edited_repo", "wrong_file_touched", "bad_validation_scope"),
        tags=("diagnose", "multi-test", "path-parsing"),
    ),
    EvalScenario(
        name="resume_session_flow",
        request="summarize this repo again",
        setup_kind="resume_flow",
        task_class="resume",
        severity="smoke",
        failure_modes=("resume_memory_loss", "no_op", "wrong_file_touched"),
        tags=("resume", "session", "memory"),
    ),
]


def run_eval_suite(
    base_session_dir: Path | None = None,
    *,
    artifact_dir: Path | None = None,
    run_label: str | None = None,
) -> EvalSummary:
    return _run_eval_scenarios(
        SCENARIOS,
        base_session_dir=base_session_dir,
        artifact_dir=artifact_dir,
        run_label=run_label,
        scenario_pack_id="built-in",
    )


def run_eval_scenario_pack(
    scenario_pack_path: Path,
    base_session_dir: Path | None = None,
    *,
    artifact_dir: Path | None = None,
    run_label: str | None = None,
) -> EvalSummary:
    pack = load_eval_scenario_pack(scenario_pack_path)
    scenarios = [
        EvalScenario(
            name=scenario.scenario_id,
            request=scenario.request,
            setup_kind=scenario.setup_kind,
            auto_approve_commands=scenario.auto_approve_commands,
            task_class=scenario.task_class,
            severity=scenario.severity,
            failure_modes=scenario.failure_modes,
            tags=scenario.tags,
        )
        for scenario in list_executable_eval_scenarios(pack)
    ]
    return _run_eval_scenarios(
        scenarios,
        base_session_dir=base_session_dir,
        artifact_dir=artifact_dir,
        run_label=run_label,
        scenario_pack_id=pack.pack_id,
    )


def _run_eval_scenarios(
    scenarios: list[EvalScenario],
    *,
    base_session_dir: Path | None,
    artifact_dir: Path | None,
    run_label: str | None,
    scenario_pack_id: str | None,
) -> EvalSummary:
    results: list[EvalResult] = []
    with TemporaryDirectory(prefix="coding-agent-v1-evals-") as tmp_dir:
        root = Path(tmp_dir)
        for scenario in scenarios:
            workspace = root / scenario.name
            workspace.mkdir(parents=True, exist_ok=True)
            _setup_workspace(workspace, scenario.setup_kind)
            session_dir = (
                base_session_dir / scenario.name
                if base_session_dir is not None
                else workspace / "sessions"
            )
            store = SessionStore(session_dir)
            started_at = time.monotonic()
            record = _run_scenario(scenario, workspace, store)
            duration_seconds = time.monotonic() - started_at
            passed, outcome_reason = _evaluate_scenario_outcome(scenario, workspace, record)
            results.append(
                EvalResult(
                    scenario_name=scenario.name,
                    passed=passed,
                    session_id=record.session_id,
                    status=record.status.value,
                    final_report=record.final_report,
                    outcome_reason=outcome_reason,
                    duration_seconds=round(duration_seconds, 6),
                    task_class=scenario.task_class,
                    severity=scenario.severity,
                    failure_modes=scenario.failure_modes,
                    tags=scenario.tags,
                )
            )
    passed_count = sum(1 for result in results if result.passed)
    summary = EvalSummary(
        total=len(results),
        passed=passed_count,
        failed=len(results) - passed_count,
        results=results,
        created_at=datetime.now(timezone.utc).isoformat(),
        run_label=run_label,
        scenario_pack_id=scenario_pack_id,
    )
    if artifact_dir is not None:
        summary.artifact_path = write_eval_summary(summary, artifact_dir)
    return summary


def summarize_eval_summary(summary: EvalSummary) -> str:
    lines = [
        f"total: {summary.total}",
        f"passed: {summary.passed}",
        f"failed: {summary.failed}",
        f"created_at: {summary.created_at}",
    ]
    if summary.scenario_pack_id is not None:
        lines.append(f"scenario_pack_id: {summary.scenario_pack_id}")
    if summary.run_label is not None:
        lines.append(f"run_label: {summary.run_label}")
    if summary.artifact_path is not None:
        lines.append(f"artifact_path: {summary.artifact_path}")
    for result in summary.results:
        outcome = "passed" if result.passed else "failed"
        lines.append(
            (
                f"{result.scenario_name}: {outcome} status={result.status} "
                f"task_class={result.task_class} duration_seconds={result.duration_seconds} "
                f"reason={result.outcome_reason} "
                f"session_id={result.session_id}"
            )
        )
    return "\n".join(lines)


def write_eval_summary(summary: EvalSummary, artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"eval-summary-{uuid4().hex}.json"
    payload = asdict(summary)
    payload["artifact_path"] = str(path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_eval_summary(path: Path) -> EvalSummary:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results = [
        EvalResult(
            scenario_name=result["scenario_name"],
            passed=bool(result["passed"]),
            session_id=result["session_id"],
            status=result["status"],
            final_report=result["final_report"],
            outcome_reason=result["outcome_reason"],
            duration_seconds=float(result["duration_seconds"]),
            task_class=result.get("task_class", "unknown"),
            severity=result.get("severity", "core"),
            failure_modes=tuple(result.get("failure_modes", [])),
            tags=tuple(result.get("tags", [])),
        )
        for result in payload["results"]
    ]
    artifact_path_value = payload.get("artifact_path")
    return EvalSummary(
        total=int(payload["total"]),
        passed=int(payload["passed"]),
        failed=int(payload["failed"]),
        results=results,
        created_at=str(payload.get("created_at", "")),
        run_label=payload.get("run_label"),
        artifact_path=Path(artifact_path_value) if artifact_path_value else None,
        scenario_pack_id=payload.get("scenario_pack_id"),
    )


def compare_eval_summaries(
    baseline: EvalSummary,
    candidate: EvalSummary,
) -> EvalComparisonSummary:
    baseline_by_name = {result.scenario_name: result for result in baseline.results}
    candidate_by_name = {result.scenario_name: result for result in candidate.results}
    scenario_names = sorted(set(baseline_by_name) | set(candidate_by_name))
    results: list[EvalComparisonResult] = []
    regressions = 0
    improvements = 0
    unchanged = 0
    for scenario_name in scenario_names:
        baseline_result = baseline_by_name.get(scenario_name)
        candidate_result = candidate_by_name.get(scenario_name)
        baseline_passed = baseline_result.passed if baseline_result is not None else False
        candidate_passed = candidate_result.passed if candidate_result is not None else False
        if baseline_passed and not candidate_passed:
            classification = "regression"
            regressions += 1
        elif not baseline_passed and candidate_passed:
            classification = "improvement"
            improvements += 1
        else:
            classification = "unchanged"
            unchanged += 1
        baseline_duration = baseline_result.duration_seconds if baseline_result is not None else 0.0
        candidate_duration = candidate_result.duration_seconds if candidate_result is not None else 0.0
        results.append(
            EvalComparisonResult(
                scenario_name=scenario_name,
                task_class=(
                    baseline_result.task_class
                    if baseline_result is not None
                    else candidate_result.task_class
                    if candidate_result is not None
                    else "unknown"
                ),
                baseline_passed=baseline_passed,
                candidate_passed=candidate_passed,
                classification=classification,
                duration_delta_seconds=round(candidate_duration - baseline_duration, 6),
                baseline_reason=baseline_result.outcome_reason if baseline_result is not None else "missing from baseline",
                candidate_reason=candidate_result.outcome_reason if candidate_result is not None else "missing from candidate",
                failure_modes=(
                    baseline_result.failure_modes
                    if baseline_result is not None and baseline_result.failure_modes
                    else candidate_result.failure_modes
                    if candidate_result is not None
                    else ()
                ),
            )
        )
    return EvalComparisonSummary(
        baseline_artifact_path=baseline.artifact_path,
        candidate_artifact_path=candidate.artifact_path,
        regressions=regressions,
        improvements=improvements,
        unchanged=unchanged,
        results=results,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def compare_eval_baseline_to_reference(
    artifact_dir: Path,
    baseline_name: str,
    *,
    candidate_reference: str = "latest-pass",
) -> EvalComparisonSummary:
    baseline_path = resolve_eval_artifact_reference(f"baseline:{baseline_name}", artifact_dir)
    candidate_path = resolve_eval_artifact_reference(candidate_reference, artifact_dir)
    baseline = load_eval_summary(baseline_path)
    candidate = load_eval_summary(candidate_path)
    return compare_eval_summaries(baseline, candidate)


def auto_promote_eval_baseline(
    artifact_dir: Path,
    baseline_name: str,
    *,
    candidate_reference: str = "latest-pass",
) -> EvalPromotionDecision:
    comparison = compare_eval_baseline_to_reference(
        artifact_dir,
        baseline_name,
        candidate_reference=candidate_reference,
    )
    if comparison.regressions > 0:
        return EvalPromotionDecision(
            baseline_name=baseline_name,
            candidate_reference=candidate_reference,
            promoted=False,
            comparison=comparison,
            artifact_path=comparison.candidate_artifact_path,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    artifact_path, config_path = promote_eval_baseline(
        artifact_dir,
        baseline_name,
        reference=candidate_reference,
    )
    return EvalPromotionDecision(
        baseline_name=baseline_name,
        candidate_reference=candidate_reference,
        promoted=True,
        comparison=comparison,
        artifact_path=artifact_path,
        config_path=config_path,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def summarize_eval_comparison(summary: EvalComparisonSummary) -> str:
    lines = [
        f"regressions: {summary.regressions}",
        f"improvements: {summary.improvements}",
        f"unchanged: {summary.unchanged}",
        f"created_at: {summary.created_at}",
    ]
    if summary.artifact_path is not None:
        lines.append(f"artifact_path: {summary.artifact_path}")
    if summary.baseline_artifact_path is not None:
        lines.append(f"baseline_artifact_path: {summary.baseline_artifact_path}")
    if summary.candidate_artifact_path is not None:
        lines.append(f"candidate_artifact_path: {summary.candidate_artifact_path}")
    for result in summary.results:
        lines.append(
            (
                f"{result.scenario_name}: {result.classification} "
                f"task_class={result.task_class} "
                f"baseline_passed={result.baseline_passed} candidate_passed={result.candidate_passed} "
                f"duration_delta_seconds={result.duration_delta_seconds}"
            )
        )
    return "\n".join(lines)


def summarize_eval_promotion_decision(decision: EvalPromotionDecision) -> str:
    lines = [
        f"baseline_name: {decision.baseline_name}",
        f"candidate_reference: {decision.candidate_reference}",
        f"promoted: {decision.promoted}",
        f"created_at: {decision.created_at}",
    ]
    if decision.artifact_path is not None:
        lines.append(f"artifact_path: {decision.artifact_path}")
    if decision.config_path is not None:
        lines.append(f"config_path: {decision.config_path}")
    if decision.decision_artifact_path is not None:
        lines.append(f"decision_artifact_path: {decision.decision_artifact_path}")
    lines.append(summarize_eval_comparison(decision.comparison))
    return "\n".join(lines)


def write_eval_comparison_summary(summary: EvalComparisonSummary, artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"eval-comparison-{uuid4().hex}.json"
    payload = _jsonify_paths(asdict(summary))
    payload["artifact_path"] = str(path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    summary.artifact_path = path
    return path


def write_eval_promotion_decision(decision: EvalPromotionDecision, artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"eval-promotion-{uuid4().hex}.json"
    payload = _jsonify_paths(asdict(decision))
    payload["decision_artifact_path"] = str(path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    decision.decision_artifact_path = path
    return path


def summarize_eval_history(summary: EvalHistorySummary) -> str:
    lines = [f"artifacts: {len(summary.artifact_paths)}"]
    for path in summary.artifact_paths:
        lines.append(f"artifact_path: {path}")
    for trend in summary.scenario_trends:
        latest_entry = trend.history[-1]
        lines.append(
            (
                f"{trend.scenario_name}: runs={trend.runs} pass_count={trend.pass_count} "
                f"fail_count={trend.fail_count} latest_passed={trend.latest_passed} "
                f"latest_duration_seconds={trend.latest_duration_seconds} "
                f"average_duration_seconds={trend.average_duration_seconds} trend={trend.trend} "
                f"latest_created_at={latest_entry.created_at} latest_run_label={latest_entry.run_label}"
            )
        )
    return "\n".join(lines)


def build_eval_artifact_index(artifact_dir: Path) -> EvalArtifactIndex:
    entries: list[EvalArtifactIndexEntry] = []
    for path in sorted(artifact_dir.glob("eval-summary-*.json")):
        summary = load_eval_summary(path)
        total = summary.total
        pass_rate = round((summary.passed / total) * 100, 2) if total else 0.0
        entries.append(
            EvalArtifactIndexEntry(
                artifact_path=path,
                created_at=summary.created_at,
                run_label=summary.run_label,
                passed=summary.passed,
                total=summary.total,
                pass_rate=pass_rate,
            )
        )
    entries.sort(key=lambda entry: entry.created_at, reverse=True)
    return EvalArtifactIndex(artifact_dir=artifact_dir, entries=entries)


def summarize_eval_artifact_index(index: EvalArtifactIndex) -> str:
    lines = [
        f"artifact_dir: {index.artifact_dir}",
        f"artifacts: {len(index.entries)}",
    ]
    for entry in index.entries:
        lines.append(
            (
                f"{entry.artifact_path.name}: created_at={entry.created_at} "
                f"run_label={entry.run_label} passed={entry.passed}/{entry.total} "
                f"pass_rate={entry.pass_rate}%"
            )
        )
    return "\n".join(lines)


def load_eval_baseline_config(artifact_dir: Path) -> EvalBaselineConfig:
    path = _baseline_config_path(artifact_dir)
    if not path.exists():
        return EvalBaselineConfig(artifact_dir=artifact_dir, baselines={})
    payload = json.loads(path.read_text(encoding="utf-8"))
    baselines = {name: Path(value) for name, value in payload.get("baselines", {}).items()}
    return EvalBaselineConfig(artifact_dir=artifact_dir, baselines=baselines)


def save_eval_baseline_reference(artifact_dir: Path, name: str, artifact_path: Path) -> Path:
    config = load_eval_baseline_config(artifact_dir)
    config.baselines[name] = artifact_path
    path = _baseline_config_path(artifact_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "baselines": {
            baseline_name: str(baseline_path)
            for baseline_name, baseline_path in sorted(config.baselines.items())
        }
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def promote_eval_baseline(
    artifact_dir: Path,
    name: str,
    *,
    reference: str = "latest-pass",
) -> tuple[Path, Path]:
    artifact_path = resolve_eval_artifact_reference(reference, artifact_dir)
    config_path = save_eval_baseline_reference(artifact_dir, name, artifact_path)
    return artifact_path, config_path


def summarize_eval_baseline_config(config: EvalBaselineConfig) -> str:
    lines = [
        f"artifact_dir: {config.artifact_dir}",
        f"baselines: {len(config.baselines)}",
    ]
    for name, path in sorted(config.baselines.items()):
        lines.append(f"{name}: {path}")
    return "\n".join(lines)


def resolve_eval_artifact_reference(reference: str, artifact_dir: Path) -> Path:
    candidate_path = Path(reference)
    if candidate_path.exists():
        return candidate_path
    baseline_match = _resolve_eval_baseline_reference(reference, artifact_dir)
    if baseline_match is not None:
        return baseline_match
    index = build_eval_artifact_index(artifact_dir)
    alias_match = _resolve_eval_artifact_alias(reference, index)
    if alias_match is not None:
        return alias_match
    matches = [entry for entry in index.entries if entry.run_label == reference]
    if not matches:
        raise ValueError(f"No eval artifact found for label: {reference}")
    if len(matches) > 1:
        raise ValueError(f"Multiple eval artifacts found for label: {reference}")
    return matches[0].artifact_path


def build_eval_history(summaries: list[EvalSummary]) -> EvalHistorySummary:
    scenario_names = sorted({result.scenario_name for summary in summaries for result in summary.results})
    trends: list[EvalScenarioTrend] = []
    artifact_paths = [summary.artifact_path for summary in summaries if summary.artifact_path is not None]
    for scenario_name in scenario_names:
        history: list[EvalHistoryEntry] = []
        durations: list[float] = []
        for summary in summaries:
            result = next((item for item in summary.results if item.scenario_name == scenario_name), None)
            if result is None:
                continue
            history.append(
                EvalHistoryEntry(
                    artifact_path=summary.artifact_path,
                    created_at=summary.created_at or None,
                    run_label=summary.run_label,
                    passed=result.passed,
                    duration_seconds=result.duration_seconds,
                    outcome_reason=result.outcome_reason,
                )
            )
            durations.append(result.duration_seconds)
        pass_count = sum(1 for entry in history if entry.passed)
        fail_count = len(history) - pass_count
        latest = history[-1]
        average_duration_seconds = round(sum(durations) / len(durations), 6)
        trend = _duration_trend(history)
        trends.append(
            EvalScenarioTrend(
                scenario_name=scenario_name,
                runs=len(history),
                pass_count=pass_count,
                fail_count=fail_count,
                latest_passed=latest.passed,
                latest_duration_seconds=latest.duration_seconds,
                average_duration_seconds=average_duration_seconds,
                trend=trend,
                history=history,
            )
        )
    return EvalHistorySummary(
        artifact_paths=[path for path in artifact_paths],
        scenario_trends=trends,
    )


def build_eval_task_class_summary(summary: EvalSummary) -> list[EvalTaskClassSummaryEntry]:
    grouped: dict[str, list[EvalResult]] = {}
    for result in summary.results:
        grouped.setdefault(result.task_class, []).append(result)
    entries: list[EvalTaskClassSummaryEntry] = []
    for task_class in sorted(grouped):
        results = grouped[task_class]
        entries.append(
            EvalTaskClassSummaryEntry(
                task_class=task_class,
                total=len(results),
                passed=sum(1 for result in results if result.passed),
                failed=sum(1 for result in results if not result.passed),
                scenario_names=tuple(sorted(result.scenario_name for result in results)),
            )
        )
    return entries


def summarize_eval_task_class_summary(entries: list[EvalTaskClassSummaryEntry]) -> str:
    lines: list[str] = []
    for entry in entries:
        lines.append(
            (
                f"{entry.task_class}: passed={entry.passed}/{entry.total} "
                f"failed={entry.failed} scenarios={','.join(entry.scenario_names)}"
            )
        )
    return "\n".join(lines)


def build_eval_failure_mode_summary(summary: EvalSummary) -> list[EvalFailureModeSummaryEntry]:
    grouped: dict[str, list[EvalResult]] = {}
    for result in summary.results:
        for failure_mode in result.failure_modes:
            grouped.setdefault(failure_mode, []).append(result)
    entries: list[EvalFailureModeSummaryEntry] = []
    for failure_mode in sorted(grouped):
        results = grouped[failure_mode]
        entries.append(
            EvalFailureModeSummaryEntry(
                failure_mode=failure_mode,
                scenario_count=len(results),
                passed=sum(1 for result in results if result.passed),
                failed=sum(1 for result in results if not result.passed),
                scenario_names=tuple(sorted(result.scenario_name for result in results)),
            )
        )
    return entries


def summarize_eval_failure_mode_summary(entries: list[EvalFailureModeSummaryEntry]) -> str:
    lines: list[str] = []
    for entry in entries:
        lines.append(
            (
                f"{entry.failure_mode}: passed={entry.passed}/{entry.scenario_count} "
                f"failed={entry.failed} scenarios={','.join(entry.scenario_names)}"
            )
        )
    return "\n".join(lines)


def build_eval_comparison_task_class_summary(
    comparison: EvalComparisonSummary,
) -> list[EvalTaskClassComparisonEntry]:
    grouped: dict[str, list[EvalComparisonResult]] = {}
    for result in comparison.results:
        grouped.setdefault(result.task_class, []).append(result)
    entries: list[EvalTaskClassComparisonEntry] = []
    for task_class in sorted(grouped):
        results = grouped[task_class]
        entries.append(
            EvalTaskClassComparisonEntry(
                task_class=task_class,
                regressions=sum(1 for result in results if result.classification == "regression"),
                improvements=sum(1 for result in results if result.classification == "improvement"),
                unchanged=sum(1 for result in results if result.classification == "unchanged"),
                scenario_names=tuple(sorted(result.scenario_name for result in results)),
            )
        )
    return entries


def summarize_eval_comparison_task_class_summary(
    entries: list[EvalTaskClassComparisonEntry],
) -> str:
    lines: list[str] = []
    for entry in entries:
        lines.append(
            (
                f"{entry.task_class}: regressions={entry.regressions} "
                f"improvements={entry.improvements} unchanged={entry.unchanged} "
                f"scenarios={','.join(entry.scenario_names)}"
            )
        )
    return "\n".join(lines)


def _setup_workspace(workspace: Path, setup_kind: str) -> None:
    if setup_kind == "repair":
        (workspace / "calc.py").write_text(
            "def add(a, b):\n    return a - b\n",
            encoding="utf-8",
        )
        (workspace / "test_calc.py").write_text(
            "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "diagnose":
        (workspace / "calc.py").write_text(
            "def add(a, b):\n    return a - b\n",
            encoding="utf-8",
        )
        (workspace / "test_calc.py").write_text(
            "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "rename":
        (workspace / "calc.py").write_text(
            "def add(a, b):\n    return a + b\n",
            encoding="utf-8",
        )
        (workspace / "test_calc.py").write_text(
            "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "cli_flag":
        (workspace / "cli.py").write_text(
            (
                "import argparse\n\n"
                "def build_parser():\n"
                '    parser = argparse.ArgumentParser(description="demo")\n'
                "    return parser\n"
            ),
            encoding="utf-8",
        )
        (workspace / "test_cli.py").write_text(
            (
                "from cli import build_parser\n\n"
                "def test_parser_accepts_verbose_flag():\n"
                "    parser = build_parser()\n"
                "    args = parser.parse_args(['--verbose'])\n"
                "    assert args.verbose is True\n"
            ),
            encoding="utf-8",
        )
        return
    if setup_kind == "single_test_cli_flag":
        (workspace / "cli.py").write_text(
            (
                "import argparse\n\n"
                "def build_parser():\n"
                '    parser = argparse.ArgumentParser(description="demo")\n'
                "    return parser\n"
            ),
            encoding="utf-8",
        )
        (workspace / "test_placeholder.py").write_text(
            "def test_placeholder():\n    assert True\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "module_aware_cli_flag":
        (workspace / "cli.py").write_text(
            (
                "import argparse\n\n"
                "def build_parser():\n"
                '    parser = argparse.ArgumentParser(description="demo")\n'
                "    return parser\n"
            ),
            encoding="utf-8",
        )
        (workspace / "test_cli.py").write_text(
            (
                "from cli import build_parser\n\n"
                "def test_parser_has_verbose_action():\n"
                "    parser = build_parser()\n"
                "    assert any(action.dest == 'verbose' for action in parser._actions)\n"
            ),
            encoding="utf-8",
        )
        (workspace / "test_other.py").write_text(
            "def test_other():\n    assert True\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "diagnose_multi_test":
        (workspace / "calc.py").write_text(
            "def add(a, b):\n    return a - b\n",
            encoding="utf-8",
        )
        first_tests = workspace / "tests" / "quoted"
        first_tests.mkdir(parents=True, exist_ok=True)
        (first_tests / "test_first.py").write_text(
            "from calc import add\n\n\ndef test_first():\n    assert add(1, 2) == 3\n",
            encoding="utf-8",
        )
        second_tests = workspace / "tests" / "linked"
        second_tests.mkdir(parents=True, exist_ok=True)
        (second_tests / "test_second.py").write_text(
            "from calc import add\n\n\ndef test_second():\n    assert add(1, 2) == 3\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "explicit_multi_test_cli_flag":
        (workspace / "cli.py").write_text(
            (
                "import argparse\n\n"
                "def build_parser():\n"
                '    parser = argparse.ArgumentParser(description="demo")\n'
                "    return parser\n"
            ),
            encoding="utf-8",
        )
        first_tests = workspace / "tests" / "regression"
        first_tests.mkdir(parents=True, exist_ok=True)
        (first_tests / "test_targeted_cli.py").write_text(
            (
                "from cli import build_parser\n\n"
                "def test_targeted_cli_regression():\n"
                "    parser = build_parser()\n"
                "    args = parser.parse_args(['--verbose'])\n"
                "    assert args.verbose is True\n"
            ),
            encoding="utf-8",
        )
        second_tests = workspace / "tests" / "smoke"
        second_tests.mkdir(parents=True, exist_ok=True)
        (second_tests / "test_cli_smoke.py").write_text(
            (
                "from cli import build_parser\n\n"
                "def test_cli_smoke():\n"
                "    parser = build_parser()\n"
                "    args = parser.parse_args(['--verbose'])\n"
                "    assert args.verbose is True\n"
            ),
            encoding="utf-8",
        )
        return
    if setup_kind == "config_option":
        (workspace / "config.py").write_text(
            'DEFAULT_CONFIG = {"mode": "basic"}\n',
            encoding="utf-8",
        )
        (workspace / "test_config.py").write_text(
            (
                "from config import DEFAULT_CONFIG\n\n"
                "def test_timeout_config():\n"
                '    assert DEFAULT_CONFIG["timeout"] == 30\n'
            ),
            encoding="utf-8",
        )
        return
    if setup_kind == "env_var":
        (workspace / "config.py").write_text(
            'import os\n\nDEFAULT_CONFIG = {"mode": os.getenv("APP_MODE", "basic")}\n',
            encoding="utf-8",
        )
        (workspace / "test_config.py").write_text(
            (
                "from config import DEFAULT_CONFIG\nimport os\n\n"
                "def test_profile_env_var():\n"
                '    assert DEFAULT_CONFIG["profile"] == os.getenv("APP_PROFILE", "advanced")\n'
            ),
            encoding="utf-8",
        )
        return
    if setup_kind == "approval_boundary":
        (workspace / "test_sample.py").write_text(
            "def test_ok():\n    assert 1 == 1\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "resume_flow":
        (workspace / "README.md").write_text("project intro", encoding="utf-8")
        return
    raise ValueError(f"Unknown eval setup kind: {setup_kind}")


def _evaluate_scenario_outcome(
    scenario: EvalScenario,
    workspace: Path,
    record: SessionRecord,
) -> tuple[bool, str]:
    final_report = record.final_report
    if scenario.setup_kind == "repair":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after repair attempt"
        if "return a + b" in (workspace / "calc.py").read_text(encoding="utf-8"):
            return True, "repaired arithmetic bug and passed validation"
        return False, "expected arithmetic fix was not applied"
    if scenario.setup_kind == "rename":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after rename attempt"
        calc_text = (workspace / "calc.py").read_text(encoding="utf-8")
        test_text = (workspace / "test_calc.py").read_text(encoding="utf-8")
        if "def plus(a, b):" in calc_text and "from calc import plus" in test_text:
            return True, "renamed symbol across source and test files and passed validation"
        return False, "expected rename edits were not applied"
    if scenario.setup_kind == "cli_flag":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after feature edit"
        cli_text = (workspace / "cli.py").read_text(encoding="utf-8")
        if 'parser.add_argument("--verbose", action="store_true", help="Enable verbose mode.")' in cli_text:
            return True, "added requested CLI flag and passed validation"
        return False, "expected CLI flag edit was not applied"
    if scenario.setup_kind == "single_test_cli_flag":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after single-test fallback feature edit"
        if record.task_plan is None:
            return False, "single-test fallback task plan was missing"
        cli_text = (workspace / "cli.py").read_text(encoding="utf-8")
        if 'parser.add_argument("--verbose", action="store_true", help="Enable verbose mode.")' not in cli_text:
            return False, "expected CLI flag edit was not applied"
        if (
            "selected validation command `pytest -q test_placeholder.py` from single-test workspace fallback"
            not in " ".join(record.task_plan.reasons)
        ):
            return False, "single-test fallback reasoning was not recorded in the task plan"
        return True, "added requested CLI flag and recorded single-test workspace fallback validation"
    if scenario.setup_kind == "module_aware_cli_flag":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after module-aware CLI feature edit"
        if record.task_plan is None:
            return False, "module-aware CLI task plan was missing"
        cli_text = (workspace / "cli.py").read_text(encoding="utf-8")
        if 'parser.add_argument("--verbose", action="store_true", help="Enable verbose mode.")' not in cli_text:
            return False, "expected CLI flag edit was not applied"
        if (
            "selected validation command `pytest -q test_cli.py` from module-aware CLI parser test evidence"
            not in " ".join(record.task_plan.reasons)
        ):
            return False, "module-aware CLI reasoning was not recorded in the task plan"
        return True, "added requested CLI flag and recorded module-aware CLI validation"
    if scenario.setup_kind == "explicit_multi_test_cli_flag":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after explicit multi-test feature edit"
        cli_text = (workspace / "cli.py").read_text(encoding="utf-8")
        if 'parser.add_argument("--verbose", action="store_true", help="Enable verbose mode.")' not in cli_text:
            return False, "expected CLI flag edit was not applied"
        if (
            "tests/regression/test_targeted_cli.py tests/smoke/test_cli_smoke.py"
            not in final_report
        ):
            return False, "explicit multi-test validation command was not preserved in the report"
        return True, "added requested CLI flag and preserved explicit multi-test validation"
    if scenario.setup_kind == "config_option":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after config feature edit"
        config_text = (workspace / "config.py").read_text(encoding="utf-8")
        if '"timeout": 30' in config_text:
            return True, "added requested config option and passed validation"
        return False, "expected config option edit was not applied"
    if scenario.setup_kind == "env_var":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after env var feature edit"
        config_text = (workspace / "config.py").read_text(encoding="utf-8")
        if '"profile": os.getenv("APP_PROFILE", "advanced")' in config_text:
            return True, "added requested environment-variable config option and passed validation"
        return False, "expected environment-variable config edit was not applied"
    if scenario.setup_kind == "approval_boundary":
        if "approval is required" not in final_report.lower():
            return False, "expected approval boundary message was missing"
        if record.task_plan is None:
            return False, "approval-boundary task plan was missing"
        if (
            "selected validation command `pytest -q` from full-suite fallback because no narrower test target was justified"
            not in " ".join(record.task_plan.reasons)
        ):
            return False, "approval-boundary scenario did not record full-suite fallback reasoning"
        if record.task_plan.validation_command == "pytest -q":
            return True, "correctly stopped on approval boundary after selecting full-suite fallback validation"
        return False, "expected approval boundary message was missing"
    if scenario.setup_kind == "diagnose":
        calc_text = (workspace / "calc.py").read_text(encoding="utf-8")
        if "Task flow: diagnose." not in final_report:
            return False, "diagnose flow report marker was missing"
        if "without applying edits" not in final_report:
            return False, "diagnose flow did not report no-edit completion"
        if "return a - b" in calc_text:
            return True, "gathered failure evidence without editing files"
        return False, "diagnose flow unexpectedly edited source files"
    if scenario.setup_kind == "diagnose_multi_test":
        calc_text = (workspace / "calc.py").read_text(encoding="utf-8")
        if "Task flow: diagnose." not in final_report:
            return False, "diagnose flow report marker was missing"
        if "without applying edits" not in final_report:
            return False, "diagnose flow did not report no-edit completion"
        if "tests/quoted/test_first.py tests/linked/test_second.py" not in final_report:
            return False, "mixed-format multi-test diagnose validation command was not preserved in the report"
        if "return a - b" in calc_text:
            return True, "gathered multi-test failure evidence without editing files"
        return False, "diagnose flow unexpectedly edited source files"
    if scenario.setup_kind == "resume_flow":
        if (
            "Resumed from session " in final_report
            and "README.md" in final_report
        ):
            return True, "resumed prior session context and produced a resumed report"
        return False, "resume flow did not carry prior session context into the report"
    return False, "unknown eval scenario kind"


def _run_scenario(scenario: EvalScenario, workspace: Path, store: SessionStore):
    if scenario.setup_kind == "resume_flow":
        first = run_session(
            "summarize this repo",
            workspace,
            store,
            auto_approve_commands=scenario.auto_approve_commands,
        )
        return run_session(
            scenario.request,
            workspace,
            store,
            auto_approve_commands=scenario.auto_approve_commands,
            resume_from_session_id=first.session_id,
        )
    return run_session(
        scenario.request,
        workspace,
        store,
        auto_approve_commands=scenario.auto_approve_commands,
    )


def _duration_trend(history: list[EvalHistoryEntry]) -> str:
    if len(history) < 2:
        return "insufficient-data"
    first = history[0].duration_seconds
    last = history[-1].duration_seconds
    delta = last - first
    if abs(delta) < 0.000001:
        return "flat"
    if delta < 0:
        return "faster"
    return "slower"


def _resolve_eval_artifact_alias(reference: str, index: EvalArtifactIndex) -> Path | None:
    if reference == "latest":
        if not index.entries:
            raise ValueError("No eval artifacts are available.")
        return index.entries[0].artifact_path
    if reference == "latest-pass":
        passing_entries = [entry for entry in index.entries if entry.passed == entry.total]
        if not passing_entries:
            raise ValueError("No fully passing eval artifacts are available.")
        return passing_entries[0].artifact_path
    if reference.startswith("latest-pass:"):
        prefix = reference.split(":", 1)[1]
        matching_entries = [
            entry
            for entry in index.entries
            if entry.passed == entry.total and entry.run_label is not None and entry.run_label.startswith(prefix)
        ]
        if not matching_entries:
            raise ValueError(f"No fully passing eval artifact found for label prefix: {prefix}")
        return matching_entries[0].artifact_path
    if reference.startswith("latest:"):
        prefix = reference.split(":", 1)[1]
        matching_entries = [
            entry
            for entry in index.entries
            if entry.run_label is not None and entry.run_label.startswith(prefix)
        ]
        if not matching_entries:
            raise ValueError(f"No eval artifact found for label prefix: {prefix}")
        return matching_entries[0].artifact_path
    return None


def _resolve_eval_baseline_reference(reference: str, artifact_dir: Path) -> Path | None:
    if not reference.startswith("baseline:"):
        return None
    name = reference.split(":", 1)[1]
    config = load_eval_baseline_config(artifact_dir)
    path = config.baselines.get(name)
    if path is None:
        raise ValueError(f"No named baseline found: {name}")
    return path


def _baseline_config_path(artifact_dir: Path) -> Path:
    return artifact_dir / "named-baselines.json"


def _jsonify_paths(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonify_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonify_paths(item) for item in value]
    return value
