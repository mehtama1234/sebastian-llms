from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import HarnessConfig
from .corpus import Benchmark, Scenario, build_default_benchmark
from .instructions import load_instructions
from .model import Attempt, run_attempt
from .verifier import verify


@dataclass(slots=True)
class ScenarioRun:
    """The scored outcome of running one scenario under one harness config."""

    scenario_id: str
    task_class: str
    config_name: str
    reported_success: bool  # what the harness tells the user
    true_success: bool  # whether the answer was actually grounded
    hallucinated: bool  # reported success without grounding
    escalated: bool  # verifier gave up rather than bluff
    attempts_used: int
    verifier_runs: int
    final_stage: str
    gold_retrieved: bool
    prompt_tokens_total: int  # tokens paid across every executed attempt
    prompt_tokens_final: int  # tokens of the selected attempt
    retrieval_ops_total: int
    latency_units: int  # deterministic work proxy (retrieval + prompt work)
    attempts: list[Attempt] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        raw = {k: getattr(self, k) for k in self.__slots__ if k != "attempts"}
        raw["attempts"] = [a.to_dict() for a in self.attempts]
        return raw


def _finalize(
    scenario: Scenario,
    config: HarnessConfig,
    executed: list[Attempt],
    accepted: Attempt | None,
    reported_success: bool,
    escalated: bool,
    verifier_runs: int,
) -> ScenarioRun:
    selected = accepted if accepted is not None else executed[-1]
    true_success = selected.grounded and reported_success
    prompt_total = sum(a.prompt_tokens for a in executed)
    ops_total = sum(a.retrieval_ops for a in executed)
    return ScenarioRun(
        scenario_id=scenario.id,
        task_class=scenario.task_class,
        config_name=config.name,
        reported_success=reported_success,
        true_success=true_success,
        hallucinated=reported_success and not true_success,
        escalated=escalated,
        attempts_used=len(executed),
        verifier_runs=verifier_runs,
        final_stage=selected.stage,
        gold_retrieved=any(a.gold_retrieved for a in executed),
        prompt_tokens_total=prompt_total,
        prompt_tokens_final=selected.prompt_tokens,
        retrieval_ops_total=ops_total,
        latency_units=ops_total + prompt_total,
        attempts=executed,
    )


def run_scenario(bench: Benchmark, scenario: Scenario, config: HarnessConfig) -> ScenarioRun:
    gold_area = bench.doc(scenario.gold_doc_id).area
    instruction = load_instructions(config.instruction_mode, gold_area)
    executed: list[Attempt] = []

    def attempt(seeds: list[int]) -> Attempt:
        a = run_attempt(bench, scenario, config, instruction, seeds)
        executed.append(a)
        return a

    if not config.verifier_enabled:
        # No selector, so extra candidates cannot be chosen between. Pool them if
        # sharing evidence, otherwise run a single attempt. Any ungrounded claim
        # ships as a (silent) hallucination — the baseline the verifier improves on.
        seeds = list(range(config.candidate_count)) if config.share_evidence else [0]
        a = attempt(seeds)
        return _finalize(scenario, config, executed, a, a.claimed_success, escalated=False, verifier_runs=0)

    # Verifier path: try candidates, then retries, accept the first grounded attempt.
    accepted: Attempt | None = None
    if config.share_evidence and config.candidate_count > 1:
        candidate_groups: list[list[int]] = [list(range(config.candidate_count))]
    else:
        candidate_groups = [[i] for i in range(config.candidate_count)]

    for group in candidate_groups:
        a = attempt(group)
        if verify(a).accepted:
            accepted = a
            break

    if accepted is None:
        retry_seed = config.candidate_count
        for _ in range(config.max_retries):
            a = attempt([retry_seed])
            retry_seed += 1
            if verify(a).accepted:
                accepted = a
                break

    if accepted is not None:
        return _finalize(scenario, config, executed, accepted, True, escalated=False, verifier_runs=len(executed))
    # Nothing verified: escalate honestly rather than ship a bluff.
    return _finalize(scenario, config, executed, None, False, escalated=True, verifier_runs=len(executed))


def run_config(bench: Benchmark, config: HarnessConfig) -> list[ScenarioRun]:
    return [run_scenario(bench, scenario, config) for scenario in bench.scenarios]


def run_default_config(config: HarnessConfig) -> list[ScenarioRun]:
    return run_config(build_default_benchmark(), config)
