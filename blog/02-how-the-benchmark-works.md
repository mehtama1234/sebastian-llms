# How the benchmark actually works

Before any experiment makes sense, you have to trust the thing you are measuring
with. This post explains the made-up repo, the tasks, and the simulated model,
and it is honest about where the simulation stops.

## Why a simulation at all

I could have wired this to a real model and a real codebase. I chose not to, for
one reason: I wanted results that are the same every time I run them.

With a real model, every run drifts a little. You can never tell if a setting
helped or if the model just had a good day. With a fixed simulation, a run is
identical down to the number. That means when a score moves, it moved because I
changed a setting, not because of luck. The lab measures the **direction and
size of a tradeoff**, which is exactly what you need to make a build decision.

The cost of this choice: the lab cannot tell you real-world accuracy. It can
tell you "the verifier helps and here is roughly how much," not "you will get
exactly 94% on your codebase." That is a fair trade for a decision tool.

## The made-up repo

The corpus is twelve short files, like a tiny service codebase: a retry policy,
an HTTP client, an auth module, a couple of caches, a config parser, a worker
pool, and so on. Each file has:

- a **body**: a sentence or two of plausible code-comment text
- a **summary**: a one-line description
- an **evidence token**: a unique marker like `EVIDENCE_RETRY_BACKOFF`

That evidence token is the whole trick. A task counts as truly solved only when
its file's evidence token makes it into the final prompt. This gives the lab a
clean, exact definition of "did the right information actually reach the model?"
No fuzzy grading, no judgment calls.

## The tasks

There are twelve tasks, each a natural-language query with one correct file.
They are built to stress different parts of the harness on purpose:

- **Synonym tasks**: the query says "retry," the file says "reattempt." Plain
  text search is blind to this; embedding search can bridge it.
- **Exact-name tasks**: the query is a specific identifier like
  `parse_config_v2`. Plain text search nails it; embedding search blurs it.
- **Guidance tasks**: the task cannot be solved without a repo instruction hint,
  so it tests whether loading instruction files pays off.
- **Hard tasks**: the right file is on the edge of being found, so a single
  search attempt is flaky. These are where trying more than once matters.

This spread is deliberate. If every task were easy, every setting would tie and
the lab would teach nothing.

## The simulated model

The model is simple and deterministic. Given a prompt, it does this:

- If the correct evidence token is in the prompt, it answers correctly and
  honestly.
- If the evidence is missing but the prompt still has *some* relevant-looking
  files, it **bluffs**: it claims success and points at the wrong thing.
- If the prompt is empty or the task needed guidance it never got, it gives up.

The bluffing behavior is the important part. Real models do this constantly:
they sound confident even when the actual answer was never in front of them. By
building bluffing into the simulation, the lab can measure whether a setting
reduces bluffing or just hides it.

## The simulated verifier (and its limit)

The verifier checks one thing: is the evidence the model cited actually in the
prompt? If yes, accept. If no, reject and retry or escalate.

Here is the honest caveat. This verifier is almost perfect at spotting bluffs,
because it can see the ground-truth evidence token. A real verifier is a second
model and gets this wrong sometimes. So the "verifier removed all bluffing"
result in a later post is an **upper bound** on how well a real verifier would
do. What is real and reusable is the *machinery* around it: reject the bluff,
retry, and escalate honestly instead of shipping a guess.

## What is real vs simulated, in one list

Real, and the parts you would keep:

- the setting space (`config.py`)
- the three search modes and how their results are fused (`retrieval.py`)
- how results become a prompt and how tokens are counted (`context.py`)
- instruction-file loading and its cost (`instructions.py`)
- the multi-attempt, retry, and give-up control flow (`harness.py`)
- the scorecards and the decision memo (`scorecard.py`, `memo.py`)

Simulated, and swappable for a real model later:

- the model that reads the prompt (`model.py`)
- the verifier that checks the answer (`verifier.py`)

Swapping in a real model is a small, contained change in those two files. The
rest of the lab does not care whether the answers came from a simulation or from
a real API.

With that groundwork, the next five posts each take one setting, run the
experiment, and report what won.
