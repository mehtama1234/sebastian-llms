from __future__ import annotations

import argparse
from pathlib import Path

from .agent_loop import run_session
from .eval_harness import (
    apply_eval_decision_artifact_prune_summary,
    apply_eval_artifact_prune_summary,
    auto_promote_eval_baseline,
    build_eval_baseline_audit_summary,
    build_eval_decision_artifact_prune_summary,
    build_eval_artifact_prune_summary,
    build_eval_artifact_index,
    build_eval_comparison_task_class_summary,
    build_eval_failure_mode_summary,
    build_eval_history,
    build_eval_task_class_summary,
    compare_eval_baseline_to_reference,
    compare_eval_summaries,
    filter_eval_artifact_index,
    filter_eval_summaries_by_pack,
    load_eval_baseline_config,
    load_eval_summary,
    promote_eval_baseline,
    repair_eval_baseline_reference,
    resolve_eval_artifact_reference,
    run_eval_scenario_pack,
    run_eval_suite,
    save_eval_baseline_reference,
    summarize_eval_baseline_audit,
    summarize_eval_decision_artifact_prune_summary,
    summarize_eval_artifact_index,
    summarize_eval_artifact_prune_summary,
    summarize_eval_baseline_config,
    summarize_eval_comparison,
    summarize_eval_comparison_task_class_summary,
    summarize_eval_failure_mode_summary,
    summarize_eval_promotion_decision,
    summarize_eval_history,
    summarize_eval_summary,
    summarize_eval_task_class_summary,
    write_eval_comparison_summary,
    write_eval_promotion_decision,
)
from .session_store import SessionStore


def _default_eval_pack_path() -> Path:
    return Path(__file__).resolve().parents[4] / "evals" / "coding-agent-v1" / "scenarios" / "core-v1.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Coding Agent V1 scaffold.")
    parser.add_argument("request", nargs="?", help="The coding request to run.")
    parser.add_argument(
        "--cwd",
        default=".",
        help="Workspace path to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--session-dir",
        default=".coding-agent-v1/sessions",
        help="Directory where session JSON files will be written.",
    )
    parser.add_argument(
        "--auto-approve-commands",
        action="store_true",
        help="Automatically approve command execution for this session.",
    )
    parser.add_argument(
        "--review-session",
        help="Load and print a saved session by id instead of running a new one.",
    )
    parser.add_argument(
        "--resume-session",
        help="Resume from a saved session id when running a new request.",
    )
    parser.add_argument(
        "--run-evals",
        action="store_true",
        help="Run the default external eval benchmark pack and print summaries.",
    )
    parser.add_argument(
        "--run-smoke-evals",
        action="store_true",
        help="Run the built-in smoke eval scenarios and print summaries.",
    )
    parser.add_argument(
        "--run-eval-pack",
        nargs="?",
        const=str(_default_eval_pack_path()),
        metavar="PACK_PATH",
        help="Run an external eval scenario pack. Defaults to the coding-agent-v1 core pack.",
    )
    parser.add_argument(
        "--eval-label",
        help="Optional label to store on a new eval artifact when using --run-evals.",
    )
    parser.add_argument(
        "--compare-evals",
        nargs=2,
        metavar=("BASELINE", "CANDIDATE"),
        help="Compare two saved eval summary JSON artifacts.",
    )
    parser.add_argument(
        "--history-evals",
        nargs="+",
        metavar="ARTIFACT",
        help="Summarize scenario trends across multiple saved eval summary JSON artifacts.",
    )
    parser.add_argument(
        "--list-evals",
        nargs="?",
        const=".coding-agent-v1/sessions/eval-artifacts",
        metavar="ARTIFACT_DIR",
        help="List saved eval artifacts by date, label, and pass rate.",
    )
    parser.add_argument(
        "--eval-pack-filter",
        action="append",
        metavar="PACK",
        help="Filter --list-evals or --history-evals to scenario-pack tiers like built-in, smoke, core, or stress.",
    )
    parser.add_argument(
        "--prune-evals",
        nargs="?",
        const=".coding-agent-v1/sessions/eval-artifacts",
        metavar="ARTIFACT_DIR",
        help="Plan pruning of saved eval summary artifacts while protecting named baselines and recent per-pack runs.",
    )
    parser.add_argument(
        "--prune-evals-apply",
        action="store_true",
        help="Apply deletions for --prune-evals instead of only printing the prune plan.",
    )
    parser.add_argument(
        "--prune-keep-per-pack",
        type=int,
        default=1,
        help="How many newest and newest-passing artifacts to retain per scenario pack when using --prune-evals.",
    )
    parser.add_argument(
        "--prune-decision-artifacts",
        nargs="?",
        const=".coding-agent-v1/sessions/eval-artifacts",
        metavar="ARTIFACT_DIR",
        help="Plan pruning of decision artifacts while protecting those that reference retained eval summaries.",
    )
    parser.add_argument(
        "--prune-decision-artifacts-apply",
        action="store_true",
        help="Apply deletions for --prune-decision-artifacts instead of only printing the prune plan.",
    )
    parser.add_argument(
        "--prune-decision-keep-per-kind",
        type=int,
        default=1,
        help="How many newest decision artifacts to retain per decision kind when using --prune-decision-artifacts.",
    )
    parser.add_argument(
        "--set-eval-baseline",
        nargs=2,
        metavar=("NAME", "REFERENCE"),
        help="Save a named baseline that points to an eval artifact reference.",
    )
    parser.add_argument(
        "--list-eval-baselines",
        nargs="?",
        const=".coding-agent-v1/sessions/eval-artifacts",
        metavar="ARTIFACT_DIR",
        help="List named eval baselines stored for an artifact directory.",
    )
    parser.add_argument(
        "--promote-eval-baseline",
        nargs="+",
        metavar=("NAME", "REFERENCE"),
        help="Promote an eval artifact reference into a named baseline. Defaults to latest-pass.",
    )
    parser.add_argument(
        "--compare-eval-baseline",
        nargs="+",
        metavar=("NAME", "REFERENCE"),
        help="Compare baseline:<NAME> against a reference. Defaults to latest-pass.",
    )
    parser.add_argument(
        "--auto-promote-eval-baseline",
        nargs="+",
        metavar=("NAME", "REFERENCE"),
        help="Promote a candidate into a baseline only if comparison shows no regressions. Defaults to latest-pass.",
    )
    parser.add_argument(
        "--repair-eval-baseline",
        nargs="+",
        metavar=("NAME", "REFERENCE"),
        help="Repair a named baseline by repointing it to a resolved artifact reference. Defaults to latest-pass within the saved baseline pack.",
    )
    parser.add_argument(
        "--audit-eval-baselines",
        nargs="?",
        const=".coding-agent-v1/sessions/eval-artifacts",
        metavar="ARTIFACT_DIR",
        help="Audit named eval baselines for missing or stale artifact targets.",
    )
    return parser


def _print_eval_summary_with_breakdowns(summary) -> None:
    print(summarize_eval_summary(summary))
    task_class_summary = build_eval_task_class_summary(summary)
    if task_class_summary:
        print("")
        print("task_class_summary:")
        print(summarize_eval_task_class_summary(task_class_summary))
    failure_mode_summary = build_eval_failure_mode_summary(summary)
    if failure_mode_summary:
        print("")
        print("failure_mode_summary:")
        print(summarize_eval_failure_mode_summary(failure_mode_summary))


def _print_eval_comparison_with_breakdowns(comparison) -> None:
    print(summarize_eval_comparison(comparison))
    task_class_summary = build_eval_comparison_task_class_summary(comparison)
    if task_class_summary:
        print("")
        print("task_class_comparison_summary:")
        print(summarize_eval_comparison_task_class_summary(task_class_summary))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    selected_eval_modes = sum(
        1
        for enabled in (
            args.run_evals,
            args.run_smoke_evals,
            bool(args.run_eval_pack),
        )
        if enabled
    )
    if selected_eval_modes > 1:
        parser.error("--run-evals, --run-smoke-evals, and --run-eval-pack are mutually exclusive")
    if args.eval_pack_filter and args.list_evals is None and not args.history_evals:
        parser.error("--eval-pack-filter can only be used with --list-evals or --history-evals")
    if args.prune_evals_apply and args.prune_evals is None:
        parser.error("--prune-evals-apply requires --prune-evals")
    if args.prune_decision_artifacts_apply and args.prune_decision_artifacts is None:
        parser.error("--prune-decision-artifacts-apply requires --prune-decision-artifacts")
    if args.prune_keep_per_pack < 1:
        parser.error("--prune-keep-per-pack must be at least 1")
    if args.prune_decision_keep_per_kind < 1:
        parser.error("--prune-decision-keep-per-kind must be at least 1")
    store = SessionStore(Path(args.session_dir))
    if args.prune_evals is not None:
        artifact_dir = Path(args.prune_evals)
        summary = build_eval_artifact_prune_summary(
            artifact_dir,
            keep_per_pack=args.prune_keep_per_pack,
        )
        print(summarize_eval_artifact_prune_summary(summary))
        if args.prune_evals_apply:
            deleted_paths = apply_eval_artifact_prune_summary(summary)
            print(f"deleted: {len(deleted_paths)}")
            for path in deleted_paths:
                print(f"deleted_artifact: {path}")
        return
    if args.prune_decision_artifacts is not None:
        artifact_dir = Path(args.prune_decision_artifacts)
        summary = build_eval_decision_artifact_prune_summary(
            artifact_dir,
            keep_per_kind=args.prune_decision_keep_per_kind,
            keep_per_pack=args.prune_keep_per_pack,
        )
        print(summarize_eval_decision_artifact_prune_summary(summary))
        if args.prune_decision_artifacts_apply:
            deleted_paths = apply_eval_decision_artifact_prune_summary(summary)
            print(f"deleted: {len(deleted_paths)}")
            for path in deleted_paths:
                print(f"deleted_artifact: {path}")
        return
    if args.repair_eval_baseline:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        if len(args.repair_eval_baseline) == 1:
            name = args.repair_eval_baseline[0]
            reference = None
        elif len(args.repair_eval_baseline) == 2:
            name, reference = args.repair_eval_baseline
        else:
            parser.error("--repair-eval-baseline expects NAME or NAME REFERENCE")
        artifact_path, config_path, reference_used = repair_eval_baseline_reference(
            artifact_dir,
            name,
            reference=reference,
        )
        print(f"repaired_baseline: {name}")
        print(f"artifact_path: {artifact_path}")
        print(f"config_path: {config_path}")
        print(f"reference_used: {reference_used}")
        return
    if args.audit_eval_baselines is not None:
        artifact_dir = Path(args.audit_eval_baselines)
        config = load_eval_baseline_config(artifact_dir)
        summary = build_eval_baseline_audit_summary(config)
        print(summarize_eval_baseline_audit(summary))
        return
    if args.auto_promote_eval_baseline:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        decision_artifact_dir = artifact_dir / "decision-artifacts"
        if len(args.auto_promote_eval_baseline) == 1:
            baseline_name = args.auto_promote_eval_baseline[0]
            candidate_reference = "latest-pass"
        elif len(args.auto_promote_eval_baseline) == 2:
            baseline_name, candidate_reference = args.auto_promote_eval_baseline
        else:
            parser.error("--auto-promote-eval-baseline expects NAME or NAME REFERENCE")
        decision = auto_promote_eval_baseline(
            artifact_dir,
            baseline_name,
            candidate_reference=candidate_reference,
        )
        write_eval_promotion_decision(decision, decision_artifact_dir)
        print(summarize_eval_promotion_decision(decision))
        return
    if args.compare_eval_baseline:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        decision_artifact_dir = artifact_dir / "decision-artifacts"
        if len(args.compare_eval_baseline) == 1:
            baseline_name = args.compare_eval_baseline[0]
            candidate_reference = "latest-pass"
        elif len(args.compare_eval_baseline) == 2:
            baseline_name, candidate_reference = args.compare_eval_baseline
        else:
            parser.error("--compare-eval-baseline expects NAME or NAME REFERENCE")
        comparison = compare_eval_baseline_to_reference(
            artifact_dir,
            baseline_name,
            candidate_reference=candidate_reference,
        )
        write_eval_comparison_summary(comparison, decision_artifact_dir)
        _print_eval_comparison_with_breakdowns(comparison)
        return
    if args.promote_eval_baseline:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        if len(args.promote_eval_baseline) == 1:
            name = args.promote_eval_baseline[0]
            reference = "latest-pass"
        elif len(args.promote_eval_baseline) == 2:
            name, reference = args.promote_eval_baseline
        else:
            parser.error("--promote-eval-baseline expects NAME or NAME REFERENCE")
        artifact_path, config_path = promote_eval_baseline(
            artifact_dir,
            name,
            reference=reference,
        )
        print(f"promoted_baseline: {name}")
        print(f"artifact_path: {artifact_path}")
        print(f"config_path: {config_path}")
        return
    if args.list_eval_baselines is not None:
        artifact_dir = Path(args.list_eval_baselines)
        config = load_eval_baseline_config(artifact_dir)
        print(summarize_eval_baseline_config(config))
        return
    if args.set_eval_baseline:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        name, reference = args.set_eval_baseline
        resolved_path = resolve_eval_artifact_reference(reference, artifact_dir)
        config_path = save_eval_baseline_reference(artifact_dir, name, resolved_path)
        print(f"saved_baseline: {name}")
        print(f"artifact_path: {resolved_path}")
        print(f"config_path: {config_path}")
        return
    if args.list_evals is not None:
        artifact_dir = Path(args.list_evals)
        index = build_eval_artifact_index(artifact_dir)
        if args.eval_pack_filter:
            index = filter_eval_artifact_index(index, args.eval_pack_filter)
        print(summarize_eval_artifact_index(index))
        return
    if args.history_evals:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        summaries = [
            load_eval_summary(resolve_eval_artifact_reference(path, artifact_dir))
            for path in args.history_evals
        ]
        if args.eval_pack_filter:
            summaries = filter_eval_summaries_by_pack(summaries, args.eval_pack_filter)
        history = build_eval_history(summaries)
        print(summarize_eval_history(history))
        return
    if args.compare_evals:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        decision_artifact_dir = artifact_dir / "decision-artifacts"
        baseline = load_eval_summary(resolve_eval_artifact_reference(args.compare_evals[0], artifact_dir))
        candidate = load_eval_summary(resolve_eval_artifact_reference(args.compare_evals[1], artifact_dir))
        comparison = compare_eval_summaries(baseline, candidate)
        write_eval_comparison_summary(comparison, decision_artifact_dir)
        _print_eval_comparison_with_breakdowns(comparison)
        return
    if args.run_evals:
        summary = run_eval_scenario_pack(
            _default_eval_pack_path(),
            Path(args.session_dir),
            artifact_dir=Path(args.session_dir) / "eval-artifacts",
            run_label=args.eval_label,
        )
        _print_eval_summary_with_breakdowns(summary)
        return
    if args.run_smoke_evals:
        summary = run_eval_suite(
            Path(args.session_dir),
            artifact_dir=Path(args.session_dir) / "eval-artifacts",
            run_label=args.eval_label,
        )
        _print_eval_summary_with_breakdowns(summary)
        return
    if args.run_eval_pack:
        summary = run_eval_scenario_pack(
            Path(args.run_eval_pack),
            Path(args.session_dir),
            artifact_dir=Path(args.session_dir) / "eval-artifacts",
            run_label=args.eval_label,
        )
        _print_eval_summary_with_breakdowns(summary)
        return
    if args.review_session:
        record = store.load(args.review_session)
        print(store.build_review_summary(record))
        return
    if not args.request:
        parser.error(
            "request is required unless --review-session, --run-evals, "
            "--compare-evals, --history-evals, --list-evals, "
            "--prune-evals, --prune-decision-artifacts, --set-eval-baseline, --list-eval-baselines, "
            "--promote-eval-baseline, --repair-eval-baseline, --audit-eval-baselines, --compare-eval-baseline, or "
            "--auto-promote-eval-baseline is used"
        )
    record = run_session(
        args.request,
        Path(args.cwd),
        store,
        auto_approve_commands=args.auto_approve_commands,
        resume_from_session_id=args.resume_session,
    )
    print(f"session_id: {record.session_id}")
    print(f"status: {record.status.value}")
    print(f"workspace_root: {record.workspace_root}")
    if record.resumed_from_session_id:
        print(f"resumed_from: {record.resumed_from_session_id}")
    print(f"final_report: {record.final_report}")
