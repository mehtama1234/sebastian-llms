from __future__ import annotations

import argparse
from pathlib import Path

from .agent_loop import run_session
from .eval_harness import (
    auto_promote_eval_baseline,
    build_eval_artifact_index,
    build_eval_history,
    compare_eval_baseline_to_reference,
    compare_eval_summaries,
    load_eval_baseline_config,
    load_eval_summary,
    promote_eval_baseline,
    resolve_eval_artifact_reference,
    run_eval_suite,
    save_eval_baseline_reference,
    summarize_eval_artifact_index,
    summarize_eval_baseline_config,
    summarize_eval_comparison,
    summarize_eval_promotion_decision,
    summarize_eval_history,
    summarize_eval_summary,
    write_eval_comparison_summary,
    write_eval_promotion_decision,
)
from .session_store import SessionStore


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
        help="Run the built-in eval scenarios and print a summary.",
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
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    store = SessionStore(Path(args.session_dir))
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
        print(summarize_eval_comparison(comparison))
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
        print(summarize_eval_artifact_index(index))
        return
    if args.history_evals:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        summaries = [
            load_eval_summary(resolve_eval_artifact_reference(path, artifact_dir))
            for path in args.history_evals
        ]
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
        print(summarize_eval_comparison(comparison))
        return
    if args.run_evals:
        summary = run_eval_suite(
            Path(args.session_dir),
            artifact_dir=Path(args.session_dir) / "eval-artifacts",
            run_label=args.eval_label,
        )
        print(summarize_eval_summary(summary))
        return
    if args.review_session:
        record = store.load(args.review_session)
        print(store.build_review_summary(record))
        return
    if not args.request:
        parser.error(
            "request is required unless --review-session, --run-evals, "
            "--compare-evals, --history-evals, --list-evals, "
            "--set-eval-baseline, --list-eval-baselines, "
            "--promote-eval-baseline, --compare-eval-baseline, or "
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
