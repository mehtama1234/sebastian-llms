# Putting it together: the production candidate

Each earlier post changed one setting and measured it. This post stacks the
winners into a single harness and asks the real question: does adding up the
individual wins actually give you one good system?

## The winners, recapped

| Axis | Winner | Why |
| --- | --- | --- |
| Retrieval | Lexical (with vector in reserve) | Cheapest, ties hybrid on honest success |
| Context | Inline full | Only policy that keeps honest success high here |
| Instructions | Hierarchical | Unlocks guidance-gated tasks, cost buys quality |
| Verifier | On | Kills bluffing, makes the system honest |
| Test-time scaling | Retry (or multi/shared) | Recovers flaky tasks, only with a verifier |

## The stacked candidate

The `production_candidate` config turns them all on at once: hybrid search, full
inlining, hierarchical instructions, the verifier, three coordinated attempts
with shared evidence, and a couple of retries. Here is how it compares to the
plain baseline we started with:

| | Baseline | Production candidate |
| --- | --- | --- |
| Honest success | 0.67 | 1.00 |
| Hallucination | 0.17 | 0.00 |
| Search cost (ops) | 70 | 570 |
| Prompt tokens | 62 | 140 |

The stack works. Honest success went from two-thirds to everything, and bluffing
went to zero. The pieces did not fight each other — better search, complete
context, the right hints, and a verifier that guards the exit combine into a
system that solves every task and never lies about the ones it cannot.

## The catch: it is not free

That quality came at real cost: about eight times the search work and more than
twice the prompt tokens. That is the honest picture of a maxed-out harness. It is
not the config you run on every trivial request. It is the config you reach for
when being right matters more than being cheap.

The point of the lab is that you can now *see* that trade instead of guessing it.
For a cheap, high-volume path you might run lexical search, full inlining, and a
verifier and stop there. For a high-stakes path you turn on the rest. Same code,
different point on the cost/quality curve, chosen on purpose.

## How the lab hands you the decision

Everything above comes out of the lab automatically:

- `llm-dev-experiment` runs the full sweep and prints the scorecard.
- `llm-dev-scorecard` prints just the per-config numbers.
- `llm-dev-memo` writes the plain-language decision memo, with a recommendation
  per axis and the reasoning behind each one.

The committed memo lives at
`projects/llm-developments-2026/experiment-findings.md`, and it regenerates from
the code, so it never drifts from what the experiments actually show.

## What this proves, and what is next

What it proves: you can take a pile of disagreeing papers, turn each claim into a
setting, and let measurement decide instead of taste. The recommendations here —
grep-first search, complete-enough context, targeted instructions, a verifier, and
attempts only where recall is flaky — are not opinions. They fell out of the
scores.

What is next, and honestly not done yet:

- **Longer tasks.** The benchmark is single-step. Real agent work is many steps,
  and the interesting failures happen across a long session.
- **A real model.** Swap the simulation in `model.py` and `verifier.py` for a real
  API and see which of these directions hold. The rest of the lab is built to not
  care where the answers come from.
- **Adopting the winners.** The last mile is feeding these defaults into the real
  coding agent in `projects/coding-agent-v1/`, so the measured wins become the
  shipped behavior.

That is the whole arc: read the papers, build the smallest honest thing that can
test them, and let the numbers pick the harness. The lab is small on purpose, but
the habit it encodes — adopt by measurement, reward honesty over confidence — is
the part worth keeping.
