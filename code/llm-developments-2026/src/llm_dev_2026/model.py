from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .config import HarnessConfig
from .context import assemble_context
from .corpus import Benchmark, Scenario
from .instructions import InstructionLoad
from .retrieval import retrieve

# Probability that a *hard* scenario's gold document is actually attended on a
# single attempt, even when retrieval ranked it in top_k. Hard tasks have flaky
# recall; independent attempts (different seeds) raise the union probability,
# which is exactly the lever multi-attempt / parallel test-time scaling pulls.
HARD_RECALL_P = 0.5

# Stage where an attempt failed, for stage-level evaluation (Target D2).
STAGE_OK = "ok"
STAGE_RETRIEVAL_MISS = "retrieval_miss"
STAGE_RECALL_FLAKY = "recall_flaky"
STAGE_CONTEXT_DROP = "context_drop"
STAGE_MISSING_GUIDANCE = "missing_guidance"


def _roll(scenario_id: str, seed: int) -> float:
    h = hashlib.sha1(f"recall:{scenario_id}:{seed}".encode()).digest()
    return int.from_bytes(h[:4], "big") / 0x100000000


def _recalled(scenario: Scenario, seed: int) -> bool:
    if scenario.difficulty != "hard":
        return True
    return _roll(scenario.id, seed) < HARD_RECALL_P


@dataclass(slots=True)
class Attempt:
    seed: int
    doc_ids: list[str]
    gold_retrieved: bool
    claimed_success: bool  # what the model asserts
    grounded: bool  # whether the gold evidence marker really reached context
    stage: str  # STAGE_* label for where it stands / failed
    prompt_tokens: int
    retrieval_ops: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "doc_ids": self.doc_ids,
            "gold_retrieved": self.gold_retrieved,
            "claimed_success": self.claimed_success,
            "grounded": self.grounded,
            "stage": self.stage,
            "prompt_tokens": self.prompt_tokens,
            "retrieval_ops": self.retrieval_ops,
        }


def _effective_docs(bench: Benchmark, scenario: Scenario, config: HarnessConfig, seeds: list[int]) -> tuple[list[str], int, bool, bool]:
    """Retrieve for one or more seeds and return the docs the model actually attends.

    Returns (doc_ids, retrieval_ops, gold_retrieved, recall_dropped) where
    ``recall_dropped`` marks a hard-scenario recall miss (gold was ranked but not
    attended). Pooling multiple seeds (``share_evidence``) unions their top_k and
    recovers gold if *any* seed both ranks and attends it.
    """
    ops = 0
    pooled: list[str] = []
    gold = scenario.gold_doc_id
    ranked_gold_anywhere = False
    attended_gold = False
    for seed in seeds:
        result = retrieve(bench, scenario.query, config.retrieval_mode, seed=seed)
        ops += result.retrieval_ops
        top = result.top_k(config.top_k)
        if gold in top:
            ranked_gold_anywhere = True
            if _recalled(scenario, seed):
                attended_gold = True
        for doc_id in top:
            if doc_id == gold and not _recalled(scenario, seed):
                continue  # ranked but not attended on this seed
            if doc_id not in pooled:
                pooled.append(doc_id)
    recall_dropped = ranked_gold_anywhere and not attended_gold
    return pooled, ops, attended_gold, recall_dropped


def run_attempt(
    bench: Benchmark,
    scenario: Scenario,
    config: HarnessConfig,
    instruction: InstructionLoad,
    seeds: list[int],
) -> Attempt:
    """Run one model attempt over one (or pooled) retrieval seed(s)."""
    doc_ids, ops, gold_retrieved, recall_dropped = _effective_docs(bench, scenario, config, seeds)
    gold_doc = bench.doc(scenario.gold_doc_id)
    context = assemble_context(
        bench,
        doc_ids,
        scenario.query,
        config.context_policy,
        instruction,
        snippet_window=config.snippet_window,
    )

    # A task that needs a repo-instruction hint the harness never loaded cannot be
    # solved; the agent does not bluff here, it simply lacks the plan.
    if not instruction.satisfies(scenario.needs_guidance):
        return Attempt(
            seed=seeds[0],
            doc_ids=doc_ids,
            gold_retrieved=gold_retrieved,
            claimed_success=False,
            grounded=False,
            stage=STAGE_MISSING_GUIDANCE,
            prompt_tokens=context.prompt_tokens,
            retrieval_ops=ops,
        )

    grounded = context.has_evidence(gold_doc.evidence_token)
    if grounded:
        stage = STAGE_OK
        claimed = True
    else:
        # Evidence never reached context. The model still asserts success whenever
        # it has *something* to point at — this is the hallucination a verifier exists
        # to catch. The stage label explains why grounding failed.
        claimed = bool(doc_ids)
        if not gold_retrieved:
            stage = STAGE_RECALL_FLAKY if recall_dropped else STAGE_RETRIEVAL_MISS
        else:
            stage = STAGE_CONTEXT_DROP

    return Attempt(
        seed=seeds[0],
        doc_ids=doc_ids,
        gold_retrieved=gold_retrieved,
        claimed_success=claimed,
        grounded=grounded,
        stage=stage,
        prompt_tokens=context.prompt_tokens,
        retrieval_ops=ops,
    )
