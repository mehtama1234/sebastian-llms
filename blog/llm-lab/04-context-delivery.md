# Context delivery: inline, snippet, or pointer?

**The question:** once you have found the right files, how much of them do you
put in the prompt? The whole file is safe but expensive. A pointer is cheap but
risky.

**The paper:** *Coding Agents Are Effective Long-Context Processors.* It treats a
coding agent as something that has to manage a token budget, not just generate
code. Every file you paste in costs money and crowds the prompt.

## The three policies

The code (`context.py`) offers three ways to turn a found file into prompt text:

- **Inline full**: paste the whole file. The needed fact is always there. Highest
  token cost.
- **Inline snippet**: paste a window of text centered on where the query matches.
  Cheaper, but if the key fact sits outside that window, it gets dropped.
- **Pointer**: paste only the one-line summary and a file path. Cheapest, but the
  fact only survives if the summary happens to contain it.

To make this a fair fight, the evidence token in each file is placed on purpose:
in some files it sits near the top where a snippet catches it, in others at the
tail where only the full file includes it, and in some it is written into the
summary so even a pointer carries it. So no policy trivially wins.

## What the run showed

| Policy | Honest success | Hallucination | Prompt tokens |
| --- | --- | --- | --- |
| Inline full (baseline) | 0.67 | 0.17 | 62 |
| Inline snippet | 0.58 | 0.25 | 47 |
| Pointer | 0.25 | 0.58 | 20 |

The shape is a straight tradeoff:

- **Full inlining is the most reliable and the most expensive.** If the file was
  found, the fact is in the prompt.
- **Snippets save about a quarter of the tokens** but drop tail-placed facts, so
  honest success falls and bluffing rises.
- **Pointers are the cheapest by far and the worst.** Honest success collapses to
  0.25 and the model bluffs on more than half the tasks, because it has a
  file path and a vague summary but not the actual fact, so it makes something up.

## The real lesson: cheap context is only cheap if the fact survives

The pointer result is the interesting one. A pointer is not "a bit worse for a lot
less money." It quietly changes the failure mode: the model still sounds
confident, but now it is guessing. Token savings that drop the key fact do not
save you anything, because the answer is wrong.

This is why the lab's context rule is written the way it is: pick the cheapest
policy that stays within a few points of full-inlining's honest success. On this
benchmark, nothing cheaper than full inlining clears that bar, so the memo keeps
full inlining. On a real system where facts are short and live in summaries,
pointers might clear it — and then you would adopt them and pocket the savings.

## The takeaway

- **Default to inlining enough of the file that the answer is actually present.**
- **Only downgrade to snippets or pointers when you can show the key facts still
  survive** the smaller window. Measure honest success, not token savings alone.
- **Watch the hallucination rate, not just the success rate.** A cheaper policy
  that turns misses into confident bluffs is worse than it looks on a plain
  pass/fail chart.

The knob is `context_policy`, and the token counts in the scorecard let you price
each choice before you ship it.
