# Sebastian LLMs

Research workspace for turning Sebastian Raschka's LLM and coding-agent materials
into runnable projects, experiments, and writeups.

The repo is organized **by topic**: each lane under `topics/` holds its own code,
docs, evals, projects, and notes together, instead of being spread across
type-based folders.

## Layout

```
sebastian-llms/
  sources/pdfs/          the source PDFs (canonical artifacts)
  sources/external/      external repos / source mappings we track against
  topics/                one self-contained folder per work lane (see below)
  blog/                  a single rendered site (build_site.py) with plain-language
                         writeups; sources grouped in blog/llm-lab and blog/deepseek
```

## Topics

- **`topics/coding-agents/`** — the flagship lane. `v1/` is the first end-to-end
  local coding-agent harness (inspect a repo, use tools, apply edits, verify,
  resume, self-evaluate). Plus `briefs/` (roadmaps and checklists), `evals/`
  (scenario packs), `scripts/`, `docs/`, and `notes/`.
- **`topics/architecture-advances-2026/`** — `code/` is a numpy experimentation
  harness for long-context architecture variants (compressed attention, KV
  sharing, mHC), with docs, evals, and project specs.
- **`topics/llm-developments-2026/`** — `code/` is a deterministic experiment
  harness that turns 2026 paper trends into measured policy decisions (retrieval,
  context assembly, repo instructions, verifier loops, test-time scaling), with a
  scorecard + adoption memo. Also drives the blog lab series.
- **`topics/agent-evals/`** — how to evaluate real agents: tool-call grading,
  multi-step trace debugging, runtime safety checks, and document/multimodal
  evaluation (docs, evals, projects).
- **`topics/qwen3-from-scratch/`** — a reference-vs-scratch parity project around
  the Qwen3 0.6B dense model (code, docs, evals, projects, notes).
- **`topics/harness-design/`** — papers and design notes on self-evolving
  coding-agent harnesses.

## The blog

`blog/` is a publishing surface, not a topic. `build_site.py` renders the
markdown in `blog/llm-lab/` (the experiment-lab series) and the rich SVG pages in
`blog/deepseek/` (the DeepSeek V3→V3.2 explainer + training-internals companion)
into a single static site under `blog/site/` (generated, gitignored).

```bash
cd blog && python3 build_site.py --serve --port 8137   # build + serve locally
```

## Running the code lanes

Each `code/` lane is a `src`-layout Python package with its own tests. Recreate a
venv per lane (the `.venv/` dirs are gitignored):

```bash
cd topics/llm-developments-2026/code
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest -q
```

`architecture-advances-2026` additionally uses optional `torch`/`hf` extras for a
handful of benchmark tests; without them those tests skip (or, for one un-guarded
smoke test, error) — the rest run on numpy alone.
