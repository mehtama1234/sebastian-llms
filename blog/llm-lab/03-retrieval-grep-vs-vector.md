# Retrieval: is grep all you need?

**The question:** to find the right file in a repo, is plain text search enough,
or do you need embeddings?

**The paper:** *Is Grep All You Need? How Agent Harnesses Reshape Agentic Search.*
Its surprising claim is that plain lexical search is often good enough for coding
agents, and the expensive vector database is not always worth it.

## The three modes

The code offers three search modes (`retrieval.py`):

- **Lexical**: score files by shared words with the query. This is grep with a
  ranking. It is great at exact words and blind to synonyms.
- **Vector**: score files by meaning, using a small concept-space embedding.
  This bridges synonyms and is weaker on exact, rare identifiers.
- **Hybrid**: run both and merge the two rankings with reciprocal-rank fusion.
  It tries to keep each mode's strengths, and it pays for two searches.

To make the difference real and not a coin flip, the lab uses a clean caricature:
the embedding only understands the ten known concepts and is completely blind to
exact identifiers, while lexical search keeps every exact word. So each mode has
a clear blind spot, and the tasks are built to poke both.

## What the run showed

| Mode | Honest success | Hallucination | Search cost (ops) |
| --- | --- | --- | --- |
| Lexical (baseline) | 0.67 | 0.17 | 70 |
| Vector | 0.58 | 0.25 | 120 |
| Hybrid | 0.67 | 0.17 | 190 |

Read that carefully:

- **Lexical is the strongest single default.** It ties hybrid on honest success
  and costs the least.
- **Vector did worse overall.** It won the synonym tasks but lost the
  exact-identifier tasks, and the identifier losses outnumbered the synonym wins
  on this benchmark. When it missed, the model bluffed, so its hallucination rate
  went up.
- **Hybrid matched lexical but cost almost three times the search work.** It did
  not find anything lexical alone missed here, so the extra cost bought nothing.

The lab flags hybrid as "regressed" for exactly this reason: same quality, more
cost is not an improvement.

## The one case vector wins

There is one task where lexical genuinely fails: the query says "retry on
timeout" but the file only ever says "reattempt" and "backoff." Lexical has no
shared words, so it ranks the right file just outside the top results and misses
it. Vector, working on meaning, puts it first.

That is the real lesson. Vector is not better or worse in general. It is better
exactly when your queries and your code use different words for the same idea.

## The takeaway

The paper's title is a good default: for repo search, grep really is most of what
you need. The lab's recommendation:

- **Default to lexical search.** It is cheap, predictable, and strong.
- **Add vector search only when you know your corpus is paraphrase-heavy** —
  natural-language questions over prose, or code where names and concepts drift
  apart.
- **Reach for hybrid when you cannot predict the query mix** and can afford to
  pay for two searches to buy robustness.

In the code, this is a one-line change: `retrieval_mode=RetrievalMode.LEXICAL`
versus `VECTOR` versus `HYBRID`. The point of the lab is that you can make that
choice from a number instead of a hunch.
