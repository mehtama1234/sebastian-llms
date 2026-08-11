"""Production-scale experiment harness for the LLMDevelopments.pdf paper map.

This package turns the "build now" experiment list from
``projects/llm-developments-2026/detailed-implementation-targets.md`` into a
runnable, deterministic measurement stack. It answers production decisions
(lexical vs vector vs hybrid retrieval, inline vs pointer context delivery,
repo-instruction loading, verifier-backed multi-attempt reasoning) by replaying
a fixed synthetic benchmark under many harness configurations and scoring the
tradeoffs.

The substrate is deterministic and dependency-light on purpose. Like the sibling
``architecture-advances-2026`` lane, the value is a repeatable comparison of
*policies*, not a hardware performance claim. Every scorecard states what its
numbers mean and do not mean.
"""

from .config import ContextPolicy, HarnessConfig, InstructionMode, RetrievalMode

__all__ = [
    "HarnessConfig",
    "RetrievalMode",
    "ContextPolicy",
    "InstructionMode",
]
