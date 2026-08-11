# Repo instructions: do AGENTS.md files help?

**The question:** those `AGENTS.md` and `CLAUDE.md` files that tell an agent how a
repo works — do they actually help, or do they just burn tokens and add noise?

**The paper:** *Evaluating AGENTS.md: Are Repository-Level Context Files Helpful
for Coding Agents?* It asks whether repo guidance earns its place, and whether it
should live in one big root file or in smaller files spread through the tree.

## The three modes

The code (`instructions.py`) models three ways to load guidance:

- **None**: no instruction file at all.
- **Root**: one file at the repo root, loaded for every task. Cheap, always on.
- **Hierarchical**: the root file plus a smaller file for the specific area of
  the repo the task touches. Costs more tokens, but the guidance is targeted.

Each mode has a token cost (root adds 20, hierarchical adds 35) and a coverage.
Some tasks in the benchmark simply cannot be solved without the right hint — they
model work where the agent needs to know a project convention it cannot guess
from the code alone. A "generic" hint is covered by the root file; an
area-specific hint is only covered by the matching hierarchical file.

## What the run showed

| Mode | Honest success | Reported success | Prompt tokens |
| --- | --- | --- | --- |
| None (baseline) | 0.67 | 0.83 | 62 |
| Root | 0.75 | 0.92 | 82 |
| Hierarchical | 0.83 | 1.00 | 97 |

Both instruction modes helped, and more guidance helped more:

- **Root guidance** unlocked the task that needed a generic hint, lifting honest
  success from 0.67 to 0.75 for 20 extra tokens per task.
- **Hierarchical guidance** unlocked the area-specific task too, reaching 0.83
  for 35 extra tokens per task.

Unlike the pointer experiment, this cost bought real quality. The tokens are not
wasted; they carry a hint the agent genuinely needed.

## Why hierarchical beat root

The task that root guidance could not solve needed a hint specific to one part of
the repo. A single root file cannot hold every area's rules without becoming huge
and mostly irrelevant to any one task. The hierarchical setup loads only the
matching area file, so the guidance is on-topic and the cost stays bounded.

This lines up with the paper's practical advice: one giant root instruction file
tends to become drag, while smaller files placed near the code they describe give
the agent the right hint at the right moment.

## The takeaway

- **Repo instruction files earn their place** when tasks depend on conventions the
  agent cannot read off the code.
- **Prefer targeted, area-level files over one huge root file.** Same idea as good
  documentation: keep it near what it describes and load it when it is relevant.
- **Still watch the token cost.** Guidance is not free; the win here is that its
  cost bought honest success, which is exactly the test every setting has to pass.

The knob is `instruction_mode`, and because the scorecard tracks both success and
tokens, you can see the trade in one line instead of arguing about it.
