from __future__ import annotations

from pathlib import Path

from llm_dev_2026.real_retrieval import retrieve_repo_chunks


def _repo_root() -> Path:
    return Path("/home/manishmehta/ui-projects/sebastian-llms/topics")


def test_real_retrieval_lexical_finds_architecture_lane_file():
    chunks = retrieve_repo_chunks(
        _repo_root(),
        "compressed attention long context tradeoffs architecture advances lane",
        mode="lexical",
        top_k=3,
    )
    assert chunks
    assert any(
        "architecture-advances-2026/docs/compressed-attention" in chunk.path
        or "compressed_attention_promotion_assessment.py" in chunk.path
        for chunk in chunks
    )


def test_real_retrieval_sparse_finds_verifier_stack_file():
    chunks = retrieve_repo_chunks(
        _repo_root(),
        "meta verifier trust adjustment llm developments",
        mode="sparse",
        top_k=2,
    )
    assert chunks
    assert any(chunk.path.endswith("meta_verifier.py") for chunk in chunks)


def test_real_retrieval_task_aware_finds_architecture_entrypoints():
    chunks = retrieve_repo_chunks(
        _repo_root(),
        "Explain how the architecture-advances-2026 lane models compressed attention and long-context tradeoffs.",
        mode="task_aware",
        task_class="inspect",
        top_k=2,
    )
    assert chunks
    paths = {chunk.path for chunk in chunks}
    assert "architecture-advances-2026/code/src/arch_adv_2026/long_context_eval.py" in paths
    assert any(path.endswith("compressed_attention_promotion_assessment.py") for path in paths)


def test_real_retrieval_lexical_finds_verifier_or_harness_code_for_diagnose_task():
    chunks = retrieve_repo_chunks(
        _repo_root(),
        "Trace how verifier and meta-verifier decisions flow through llm-developments-2026 and identify what is still simulated.",
        mode="lexical",
        top_k=4,
    )
    assert chunks
    assert any(
        chunk.path.endswith("verifier.py")
        or chunk.path.endswith("meta_verifier.py")
        or chunk.path.endswith("harness.py")
        for chunk in chunks
    )


def test_real_retrieval_sparse_finds_benchmark_loader_or_schema_test_for_bug_fix_task():
    chunks = retrieve_repo_chunks(
        _repo_root(),
        "Extend the benchmark loader and keep the benchmark schema tests green.",
        mode="sparse",
        top_k=4,
    )
    assert chunks
    assert any(
        chunk.path.endswith("benchmark_loader.py")
        or chunk.path.endswith("test_benchmark_schema.py")
        for chunk in chunks
    )
