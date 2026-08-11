# Why this lab exists and how it works

## The problem

There is a big pile of 2026 papers about how to make language-model agents
better. Some say lexical search beats vector search. Some say repo instruction
files help. Some say a verifier stops mistakes. Some say running the model many
times and picking the best answer is worth the extra cost.

Reading them is easy. Deciding what to actually build is hard. Papers disagree,
each one tests on its own setup, and none of them tell you what to do in *your*
harness.

So instead of writing another summary, I built a small lab that runs these ideas
as real experiments and scores them. The rule is simple: an idea only gets
adopted if it makes the harness measurably better, not just because a paper
liked it.

## What the lab is

The lab lives in `code/llm-developments-2026/`. It does one thing: it takes a
fixed set of tasks over a small code repo, runs them under many different
harness settings, and reports which settings won.

A "harness setting" is a bundle of choices:

- how to search the repo (lexical, vector, or both)
- how to put search results into the prompt (whole file, a snippet, or a pointer)
- whether to load repo instruction files (none, one root file, or nested files)
- whether to check the answer with a verifier before trusting it
- whether to try several times and pick the best

All of these live in one small object called `HarnessConfig`. Every experiment
is just "change one setting, rerun the tasks, compare the scores."

## The five questions it answers

Each question maps to one real paper and one setting in the code:

| Question | Paper | Setting |
| --- | --- | --- |
| Is plain text search enough, or do you need embeddings? | Is Grep All You Need? | `retrieval_mode` |
| Should results go in the prompt whole, or as a pointer? | Coding Agents Are Effective Long-Context Processors | `context_policy` |
| Do repo instruction files help or just cost tokens? | Evaluating AGENTS.md | `instruction_mode` |
| Can a cheap check stop the model from making things up? | Learning to Self-Verify | `verifier_enabled` |
| Do more attempts beat one attempt? | PaCoRe / Share More, Search Less | `candidate_count`, `max_retries` |

## How a single run works

For one task and one setting, the lab does this:

1. **Search** the repo for the task's query and take the top few files.
2. **Assemble** those files into a prompt, following the context policy.
3. **Answer**: a simulated model reads the prompt and either finds the needed
   fact or bluffs.
4. **Verify** (optional): a checker asks "is this answer actually backed by the
   prompt?" If not, it retries or gives up honestly.
5. **Score**: record whether the answer was really correct, whether the model
   bluffed, how many tokens it cost, and where it failed if it failed.

Run that for every task and every setting, add up the scores, and you get a
scorecard. Compare scorecards and you get a decision.

## What "better" means here

The lab is strict about one thing: it separates **what the model claimed** from
**what was actually true**.

- *Reported success*: the model said it solved the task.
- *Honest success*: the answer was really backed by the repo.
- *Hallucination*: the model claimed success but had no real evidence.

A setting that raises reported success while also raising hallucinations is not
better. It is just more confident. The lab only rewards honest success and
punishes bluffing. That single distinction drives every recommendation in this
series.

## How to run it yourself

```bash
cd code/llm-developments-2026
python -m venv .venv && .venv/bin/pip install numpy pytest
.venv/bin/python -m pytest -q                   # 37 tests
.venv/bin/python -m llm_dev_2026.cli            # the full scorecard
.venv/bin/python -m llm_dev_2026.memo_cli       # the plain-language memo
```

The next post explains how the made-up repo and the simulated model work, and
why using a simulation is the honest choice here rather than a shortcut.
