# Test-time scaling: more tries, better answers?

**The question:** if one attempt is flaky, does trying several times and keeping
the best one actually help? And what is the cheapest way to do it?

**The papers:** *PaCoRe: Learning to Scale Test-Time Compute with Parallel
Coordinated Reasoning* and *Share More, Search Less: Collaborative Parallel
Thinking.* Both are about spending more compute at answer time, in a coordinated
way, instead of just once.

## Why one attempt is flaky

Some tasks in the benchmark are marked "hard." For these, even when search ranks
the right file in the top results, a single attempt does not always actually
attend to it — it models the way a real agent sometimes overlooks the right file
on any given pass. So one attempt has about a coin-flip chance of using the key
file.

That is the setup where trying more than once should pay off: each attempt uses a
slightly different search ordering, so a file missed on one attempt can show up on
another.

## The three ways to spend more attempts

All three need the verifier from the last post, because you need a way to tell
which attempt actually got it right:

- **Multi-attempt** (`candidate_count=3`): run three separate attempts, accept the
  first one the verifier approves.
- **Retry** (`max_retries=3`): run one attempt; if the verifier rejects it, try
  again with a fresh search, up to three times.
- **Shared evidence** (`share_evidence=True`): run several searches, pool all their
  found files into one prompt, and reason over the combined set once.

## What the run showed

| Setting | Honest success | Attempts used | Search cost (ops) |
| --- | --- | --- | --- |
| Single verified attempt | 0.67 | 1.0 | 70 |
| Multi-attempt | 0.75 | 1.6 | 114 |
| Retry | 0.75 | 1.8 | 133 |
| Shared evidence | 0.75 | 1.0 | 210 |

All three lifted honest success from 0.67 to 0.75 by recovering the flaky hard
tasks. None of them added any bluffing, because the verifier still guards the
exit. They differ mostly in how they spend the extra work:

- **Multi-attempt and retry** cost more *attempts* (1.6 and 1.8 on average) but
  each attempt is cheap. Retry only pays the extra cost on the tasks that need it,
  because it stops as soon as one attempt passes.
- **Shared evidence** stays at one attempt but pays more *search and prompt* cost,
  because it pools several searches into one bigger prompt.

## The lesson: extra attempts only help with a judge

The reason all three worked is the verifier. Without a way to check answers, three
attempts are useless — you would not know which one to keep, so you would just
pick the first and pay triple for nothing. This is why the code refuses to select
between attempts unless the verifier is on.

That matches the papers' framing: test-time scaling is not "run it more times and
hope." It is "run it more times *and have a way to recognize the good result*."
The coordination is the point, not the raw repetition.

## The lesson: match the method to the failure

The three methods are not ranked; they fit different situations.

- **Retry** is the frugal default. It costs nothing extra on easy tasks and only
  spends more where the first attempt failed.
- **Multi-attempt** is good when you want a fixed, predictable amount of parallel
  work regardless of task.
- **Shared evidence** helps when the problem is that no single search finds
  everything, so pooling several searches into one view is what unlocks the task.

## The takeaway

- **More attempts help on flaky tasks, and not at all on easy ones** — so spend
  them where recall is shaky, not everywhere.
- **Never scale attempts without a verifier.** The judge is what turns extra
  compute into extra quality instead of extra cost.
- **Prefer retry as the default** because it only pays when it has to; reach for
  parallel or shared-evidence when the failure shape calls for it.
