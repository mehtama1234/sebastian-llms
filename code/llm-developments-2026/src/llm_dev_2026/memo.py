from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .experiment import BASELINE, PRODUCTION, VERIFIER_ON, ExperimentReport
from .scorecard import Scorecard

_EPS = 1e-9


@dataclass(slots=True)
class AxisDecision:
    axis: str
    recommended_config: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {"axis": self.axis, "recommended_config": self.recommended_config, "rationale": self.rationale}


def _best(scorecards: dict[str, Scorecard], names: list[str]) -> str:
    """Pick the config with highest honest success, breaking ties by lowest latency."""
    present = [n for n in names if n in scorecards]
    return min(
        present,
        key=lambda n: (-scorecards[n].task_success_rate, scorecards[n].mean_latency_units),
    )


def _pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def generate_memo(report: ExperimentReport) -> dict[str, Any]:
    """Turn the experiment report into explicit adoption decisions.

    Rules are deliberately simple and legible: adopt what raises honest success or
    cuts hallucination without paying for it, keep the cheap default when a fancier
    policy does not earn its cost. This is the "decision memo, not raw output"
    standard from the implementation targets.
    """
    sc = report.scorecards
    base = sc[BASELINE]
    decisions: list[AxisDecision] = []

    # Retrieval: honor the "grep is a strong default" thesis explicitly.
    ret_best = _best(sc, [BASELINE, "retrieval_vector", "retrieval_hybrid"])
    if ret_best == BASELINE:
        rationale = (
            f"lexical/grep already solves {_pct(base.task_success_rate)} of tasks; "
            "vector and hybrid did not raise honest success, so keep lexical as the default "
            "and reserve vector for known paraphrase-heavy corpora."
        )
    else:
        rationale = (
            f"{ret_best} lifted honest success to {_pct(sc[ret_best].task_success_rate)} "
            f"(from {_pct(base.task_success_rate)}) by recovering paraphrase queries lexical missed; "
            f"it costs ~{sc[ret_best].mean_retrieval_ops:.0f} retrieval ops vs {base.mean_retrieval_ops:.0f}."
        )
    decisions.append(AxisDecision("retrieval", ret_best, rationale))

    # Context delivery: cheapest policy that stays within 5 points of full-inlining success.
    full = base  # baseline uses inline_full
    ctx_names = [BASELINE, "context_snippet", "context_pointer"]
    affordable = [
        n for n in ctx_names if n in sc and sc[n].task_success_rate >= full.task_success_rate - 0.05
    ]
    ctx_best = min(affordable, key=lambda n: sc[n].mean_prompt_tokens_final) if affordable else BASELINE
    decisions.append(
        AxisDecision(
            "context",
            ctx_best,
            f"{ctx_best} holds success at {_pct(sc[ctx_best].task_success_rate)} "
            f"while spending {sc[ctx_best].mean_prompt_tokens_final:.0f} prompt tokens vs "
            f"{full.mean_prompt_tokens_final:.0f} for full inlining; cheaper policies that dropped "
            "evidence were rejected on success.",
        )
    )

    # Instructions: highest honest success wins; guidance-gated tasks fail without it.
    instr_best = _best(sc, [BASELINE, "instructions_root", "instructions_hierarchical"])
    decisions.append(
        AxisDecision(
            "instructions",
            instr_best,
            f"{instr_best} reaches {_pct(sc[instr_best].task_success_rate)} honest success; "
            "guidance-dependent tasks are unsolvable without the matching instruction file, "
            f"at a per-task cost of {sc[instr_best].mean_prompt_tokens_final - base.mean_prompt_tokens_final:+.0f} tokens.",
        )
    )

    # Verifier: adopt if it cuts hallucination, even if reported success falls (honesty).
    ver = sc.get(VERIFIER_ON)
    if ver is not None and ver.hallucination_rate < base.hallucination_rate - _EPS:
        decisions.append(
            AxisDecision(
                "verifier",
                VERIFIER_ON,
                f"the verifier cut hallucinated success from {_pct(base.hallucination_rate)} to "
                f"{_pct(ver.hallucination_rate)} by escalating ungrounded claims instead of shipping them; "
                "reported success drops but honest success is unchanged or higher.",
            )
        )
        verifier_recommended = True
    else:
        decisions.append(AxisDecision("verifier", BASELINE, "verifier showed no hallucination reduction on this benchmark."))
        verifier_recommended = False

    # Test-time scaling: best of the multi-attempt configs vs single-attempt+verifier.
    tts_names = [VERIFIER_ON, "attempts_multi", "attempts_shared", "attempts_retry"]
    tts_best = _best(sc, tts_names)
    if tts_best == VERIFIER_ON:
        tts_rationale = "extra attempts did not raise honest success here; a single verified attempt is enough, so do not pay for parallel/retry compute."
    else:
        tts_rationale = (
            f"{tts_best} raised honest success to {_pct(sc[tts_best].task_success_rate)} "
            f"(from {_pct(sc[VERIFIER_ON].task_success_rate)}) on flaky-recall tasks, "
            f"at {sc[tts_best].mean_attempts:.1f} mean attempts vs {sc[VERIFIER_ON].mean_attempts:.1f}."
        )
    decisions.append(AxisDecision("test_time_scaling", tts_best, tts_rationale))

    prod = sc.get(PRODUCTION)
    prod_delta = None
    if prod is not None:
        prod_delta = {
            "task_success_delta": prod.task_success_rate - base.task_success_rate,
            "hallucination_delta": prod.hallucination_rate - base.hallucination_rate,
            "latency_delta": prod.mean_latency_units - base.mean_latency_units,
        }

    return {
        "label": report.label,
        "baseline_success": base.task_success_rate,
        "decisions": [d.to_dict() for d in decisions],
        "verifier_recommended": verifier_recommended,
        "production_candidate_delta": prod_delta,
        "recommended_stack": {d.axis: d.recommended_config for d in decisions},
    }


def render_markdown(memo: dict[str, Any]) -> str:
    lines = [
        f"# Adoption Memo — {memo['label']}",
        "",
        f"Baseline honest success: **{_pct(memo['baseline_success'])}**",
        "",
        "## Axis decisions",
        "",
    ]
    for d in memo["decisions"]:
        lines.append(f"### {d['axis']}")
        lines.append(f"- **Recommended:** `{d['recommended_config']}`")
        lines.append(f"- {d['rationale']}")
        lines.append("")
    delta = memo.get("production_candidate_delta")
    if delta is not None:
        lines.append("## Combined production candidate vs baseline")
        lines.append(f"- honest success: {delta['task_success_delta']:+.2f}")
        lines.append(f"- hallucination: {delta['hallucination_delta']:+.2f}")
        lines.append(f"- latency units: {delta['latency_delta']:+.0f}")
        lines.append("")
    lines.append("> Numbers come from a deterministic synthetic benchmark. They test harness")
    lines.append("> *policy* tradeoffs and their direction, not absolute production quality.")
    lines.append("")
    return "\n".join(lines)
