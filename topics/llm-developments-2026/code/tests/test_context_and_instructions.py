from __future__ import annotations

from llm_dev_2026.config import ContextPolicy, InstructionMode
from llm_dev_2026.context import assemble_context
from llm_dev_2026.instructions import AREA_GUIDE_TOKENS, ROOT_GUIDE_TOKENS, load_instructions


def _none():
    return load_instructions(InstructionMode.NONE, "net")


def test_inline_full_always_includes_evidence(bench):
    doc = bench.doc("http_client")  # tail-evidence doc
    ctx = assemble_context(bench, ["http_client"], "http client", ContextPolicy.INLINE_FULL, _none())
    assert ctx.has_evidence(doc.evidence_token)


def test_pointer_is_cheaper_than_inline_full(bench):
    ids = ["http_client"]
    full = assemble_context(bench, ids, "http client", ContextPolicy.INLINE_FULL, _none())
    pointer = assemble_context(bench, ids, "http client", ContextPolicy.POINTER, _none())
    assert pointer.context_tokens < full.context_tokens


def test_tail_evidence_survives_full_but_not_pointer(bench):
    # deadline_guard: i=11 -> tail evidence, not in summary.
    doc = bench.doc("deadline_guard")
    assert doc.evidence_head is False and doc.evidence_in_summary is False
    full = assemble_context(bench, [doc.id], "deadline_guard_v3", ContextPolicy.INLINE_FULL, _none())
    pointer = assemble_context(bench, [doc.id], "deadline_guard_v3", ContextPolicy.POINTER, _none())
    assert full.has_evidence(doc.evidence_token)
    assert not pointer.has_evidence(doc.evidence_token)


def test_summary_evidence_reaches_pointer_context(bench):
    # retry_policy: i=0 -> evidence in head and summary.
    doc = bench.doc("retry_policy")
    assert doc.evidence_in_summary is True
    pointer = assemble_context(bench, [doc.id], "reattempt backoff", ContextPolicy.POINTER, _none())
    assert pointer.has_evidence(doc.evidence_token)


def test_instruction_costs_and_coverage():
    none = load_instructions(InstructionMode.NONE, "net")
    root = load_instructions(InstructionMode.ROOT, "net")
    hier = load_instructions(InstructionMode.HIERARCHICAL, "net")

    assert none.token_cost == 0
    assert root.token_cost == ROOT_GUIDE_TOKENS
    assert hier.token_cost == ROOT_GUIDE_TOKENS + AREA_GUIDE_TOKENS

    assert none.satisfies(None)
    assert not none.satisfies("generic")
    assert root.satisfies("generic")
    assert not root.satisfies("net")  # root cannot cover an area-specific need
    assert hier.satisfies("generic") and hier.satisfies("net")
    assert not hier.satisfies("auth")  # only the loaded area is covered


def test_instruction_tokens_flow_into_prompt(bench):
    hier = load_instructions(InstructionMode.HIERARCHICAL, "net")
    ctx = assemble_context(bench, ["http_client"], "http client", ContextPolicy.POINTER, hier)
    assert ctx.instruction_tokens == hier.token_cost
    assert ctx.prompt_tokens == ctx.context_tokens + ctx.instruction_tokens
