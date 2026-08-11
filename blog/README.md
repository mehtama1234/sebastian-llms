# Blog: building an experiment lab for 2026 LLM papers

This is a plain-language series about the code in `code/llm-developments-2026/`
and the experiments it runs. It starts from the question "which ideas from the
2026 paper pile are actually worth adopting?" and ends with a harness that
answers that question by measurement instead of taste.

Read them in order, or jump to the experiment you care about.

**Also here:** [DeepSeek V3 → V3.2, illustrated](deepseek-illustrated.html) — a picture-first walk
through Raschka's DeepSeek review, with detailed SVG diagrams for MLA, DSA sparse attention, the
generator/verifier/meta-verifier setup, self-refinement, RL reward routing, and mHC.

1. [Why this lab exists and how it works](01-why-this-lab-exists.md)
2. [How the benchmark actually works](02-how-the-benchmark-works.md)
3. [Retrieval: is grep all you need?](03-retrieval-grep-vs-vector.md)
4. [Context delivery: inline, snippet, or pointer?](04-context-delivery.md)
5. [Repo instructions: do AGENTS.md files help?](05-repo-instructions.md)
6. [The verifier: how to stop a model from bluffing](06-verifier-and-bluffing.md)
7. [Test-time scaling: more tries, better answers?](07-test-time-scaling.md)
8. [Putting it together: the production candidate](08-putting-it-together.md)

## One honest note up front

Every number in this series comes from a small, made-up code repo and a
simulated model. The lab measures the **direction** of each tradeoff, not
real-world quality. When a post says "the verifier removed all hallucinations,"
read it as "the verifier mechanism works and points the right way," not "this
exact percentage will hold with a real model." Post 2 explains why the lab is
built this way and where the simulation ends.
