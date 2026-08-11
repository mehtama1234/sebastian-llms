from __future__ import annotations

from llm_dev_2026.config import ContextPolicy, HarnessConfig, RetrievalMode
from llm_dev_2026.harness import run_config, run_scenario
from llm_dev_2026.model import STAGE_OK, Attempt
from llm_dev_2026.verifier import verify


def _grounded(grounded: bool) -> Attempt:
    return Attempt(
        seed=0, doc_ids=["d"], gold_retrieved=True, claimed_success=grounded,
        grounded=grounded, stage=STAGE_OK if grounded else "context_drop",
        prompt_tokens=10, retrieval_ops=5,
    )


def test_verifier_accepts_grounded_rejects_bluff():
    assert verify(_grounded(True)).accepted is True
    out = verify(_grounded(False))
    assert out.accepted is False and out.reason.startswith("ungrounded")


def test_true_success_implies_reported_success(bench):
    for config in [
        HarnessConfig("b"),
        HarnessConfig("v", verifier_enabled=True),
        HarnessConfig("p", context_policy=ContextPolicy.POINTER),
    ]:
        for run in run_config(bench, config):
            if run.true_success:
                assert run.reported_success


def test_verifier_removes_all_hallucinations(bench):
    baseline = run_config(bench, HarnessConfig("b"))
    verified = run_config(bench, HarnessConfig("v", verifier_enabled=True))
    assert any(r.hallucinated for r in baseline)  # baseline ships some bluffs
    assert not any(r.hallucinated for r in verified)  # verifier ships none


def test_escalation_only_under_verifier(bench):
    baseline = run_config(bench, HarnessConfig("b"))
    assert not any(r.escalated for r in baseline)
    verified = run_config(bench, HarnessConfig("v", verifier_enabled=True))
    assert any(r.escalated for r in verified)  # some bluffs become honest escalations


def test_pointer_policy_drops_tail_evidence_tasks(bench):
    runs = {r.scenario_id: r for r in run_config(bench, HarnessConfig("p", context_policy=ContextPolicy.POINTER))}
    # deadline_guard evidence is tail-only; pointer cannot deliver it -> not truly solved.
    assert runs["s_deadline_id"].true_success is False


def test_multi_attempt_helps_flaky_recall(bench):
    single = {r.scenario_id: r for r in run_config(bench, HarnessConfig("v", verifier_enabled=True))}
    retry = {
        r.scenario_id: r
        for r in run_config(bench, HarnessConfig("r", verifier_enabled=True, max_retries=4))
    }
    # A hard (flaky-recall) scenario the single verified attempt can miss should be
    # recoverable with more attempts, and never regress.
    hard_ids = [s.id for s in bench.scenarios if s.difficulty == "hard"]
    assert hard_ids
    for sid in hard_ids:
        assert retry[sid].true_success or not single[sid].true_success
    assert sum(retry[s].true_success for s in retry) >= sum(single[s].true_success for s in single)


def test_run_scenario_is_deterministic(bench):
    scenario = bench.scenarios[0]
    cfg = HarnessConfig("v", verifier_enabled=True, candidate_count=3, max_retries=2)
    assert run_scenario(bench, scenario, cfg).to_dict() == run_scenario(bench, scenario, cfg).to_dict()


def test_shared_evidence_costs_more_tokens_than_single(bench):
    scenario = next(s for s in bench.scenarios if s.difficulty == "hard")
    shared = run_scenario(
        bench, scenario, HarnessConfig("s", verifier_enabled=True, candidate_count=3, share_evidence=True)
    )
    single = run_scenario(bench, scenario, HarnessConfig("v", verifier_enabled=True))
    assert shared.prompt_tokens_final >= single.prompt_tokens_final
