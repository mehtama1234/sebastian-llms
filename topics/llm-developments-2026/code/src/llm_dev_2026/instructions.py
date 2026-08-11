from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import InstructionMode

# Token cost of loading each guidance file. Root guidance is cheap and loads on
# every task; area guidance adds cost but only helps the matching subtree. These
# costs are what the "Evaluating AGENTS.md" experiment trades against task success.
ROOT_GUIDE_TOKENS = 20
AREA_GUIDE_TOKENS = 15


@dataclass(slots=True)
class InstructionLoad:
    """The guidance made available to a task under an instruction policy."""

    mode: str
    provided: frozenset[str]  # guidance keys satisfied ("generic" and/or an area)
    token_cost: int

    def satisfies(self, needs_guidance: str | None) -> bool:
        return needs_guidance is None or needs_guidance in self.provided

    def to_dict(self) -> dict[str, Any]:
        return {"mode": self.mode, "provided": sorted(self.provided), "token_cost": self.token_cost}


def load_instructions(mode: InstructionMode, area: str) -> InstructionLoad:
    """Resolve which guidance a task gets and what it costs.

    - ``none``: nothing loaded; guidance-dependent tasks cannot be solved.
    - ``root``: one generic root file, loaded everywhere; covers ``generic`` needs.
    - ``hierarchical``: root file plus the one area file matching the task; covers
      ``generic`` and this task's area, at a higher per-task token cost.
    """
    if mode is InstructionMode.NONE:
        return InstructionLoad(mode.value, frozenset(), 0)
    if mode is InstructionMode.ROOT:
        return InstructionLoad(mode.value, frozenset({"generic"}), ROOT_GUIDE_TOKENS)
    if mode is InstructionMode.HIERARCHICAL:
        return InstructionLoad(
            mode.value,
            frozenset({"generic", area}),
            ROOT_GUIDE_TOKENS + AREA_GUIDE_TOKENS,
        )
    raise ValueError(f"unknown instruction mode: {mode}")  # pragma: no cover
