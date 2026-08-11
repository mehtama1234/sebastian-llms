# The verifier: how to stop a model from bluffing

**The question:** models sound confident even when they are wrong. Can a cheap
second check catch the bluff before you ship it?

**The paper:** *Learning to Self-Verify Makes Language Models Better Reasoners.*
The idea is that a verification step is one of the cheapest ways to make a system
more reliable without retraining anything.

## The bluff problem, in numbers

Go back to the baseline from the earlier posts:

- Reported success: 0.83
- Honest success: 0.67
- Hallucination: 0.17

That gap between 0.83 and 0.67 is the problem. On 17% of tasks the model said "I
solved it" when the real evidence was never in the prompt. Without a check, you
would believe it. Those are the confident wrong answers that make agents
dangerous in production.

## What the verifier does

The verifier (`verifier.py`) asks one question: **is the answer the model gave
actually backed by the prompt?** If yes, accept it. If no, the model was bluffing,
so reject it. When a bluff is rejected and there is nothing left to try, the
harness escalates — it reports failure honestly instead of shipping the guess.

The key design choice is in the harness (`harness.py`): a rejected bluff never
counts as success. The system would rather say "I could not do this" than hand
you a confident wrong answer.

## What the run showed

| Setting | Honest success | Reported success | Hallucination |
| --- | --- | --- | --- |
| Baseline (no verifier) | 0.67 | 0.83 | 0.17 |
| Verifier on | 0.67 | 0.67 | 0.00 |

Look at what moved:

- **Hallucination went from 0.17 to 0.00.** Every bluff got caught.
- **Reported success dropped from 0.83 to 0.67** — and that is the point. The
  reported number came down to meet the honest number. The system stopped lying to
  itself.
- **Honest success stayed the same at 0.67.** The verifier did not solve more
  tasks. It just stopped pretending it had.

## Why "reported success dropped" is a win

This is the counterintuitive result and the most important one in the series. A
naive dashboard would show reported success falling and call the verifier a
regression. The lab calls it an improvement, because it scores honesty, not
confidence.

A system that says "I solved 67% and I am not sure about the rest" is far more
useful than one that says "I solved 83%" when 16 of those points are made up. The
first one you can trust and build on. The second one fails silently in
production, which is the worst way to fail.

## The honest caveat

As post 2 said, this verifier can see the ground-truth evidence, so it catches
every bluff. A real verifier is another model and would miss some. So treat the
"hallucination went to zero" as the best case. What carries over to a real system
regardless is the shape: **check before you trust, and escalate instead of
bluffing.** Even an imperfect verifier that catches half the bluffs is a large
reliability win for very little cost.

## The takeaway

- **Add a verifier.** It is cheap and it converts confident wrong answers into
  honest "I could not do this," which is what you want in production.
- **Judge it on hallucination and honest success, not reported success.** The
  reported number is supposed to fall; that is the lie leaving the system.
- **Pair it with retries** so a caught bluff gets another shot before it
  escalates. That is the next post.
