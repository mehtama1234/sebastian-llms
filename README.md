# Sebastian LLMs

Research workspace for reviewing Sebastian Raschka's LLM and coding-agent materials and turning them into launchable projects.

## Big-Picture Learning Goal

This repo is meant to teach one core idea:

how to turn an LLM from "something that talks about code" into "something that can do bounded engineering work."

That means learning how to build the full harness around the model:

- workspace awareness
- tool use
- permissions and safety
- validation and test reruns
- memory and session logging
- evaluation and task quality

The end result is not just a chatbot for code.

The end result is a coding system that can inspect a repo, make changes, verify them, and explain what happened.

## Current Focus

The first anchor document is `CodingAgents.pdf`, which is the best starting point for project work because it describes stable coding-agent architecture rather than fast-changing setup instructions.

There is now a second concrete implementation track:

- `Qwen3fromscratch.pdf`

That track is for building a reference-vs-scratch parity project around the Qwen3 0.6B dense model so this repo contains at least one model-architecture implementation effort in addition to the coding-agent harness work.

The best companion planning docs for that topic right now are:

- `projects/coding-agent-current-status.md`
- `projects/coding-agent-git-launch-plan.md`
- `projects/coding-agent-v1-first-milestone-checklist.md`
- `projects/coding-agent-v1-release-prep.md`
- `projects/coding-agent-v1-commit-stack-plan.md`
- `projects/coding-agent-v1-planner-and-eval-upgrade.md`
- `projects/coding-agent-portfolio-roadmap.md`
- `projects/coding-agent-flagship-capstone.md`
- `projects/coding-agent-v1-gap-analysis.md`
- `projects/coding-agent-from-scratch-implementation-map.md`

## Current Flagship Build

The main implementation target in this repo right now is:

- `projects/coding-agent-v1/`

That project is the first end-to-end local harness. Its purpose is to show the minimum serious shape of a coding agent:

- inspect a repo
- read and search files
- run bounded commands
- classify explicit and natural-language requests into inspect, fix, feature, rename, and diagnose flows with scored task-flow selection informed by workspace structure and test evidence
- apply targeted edits
- implement a small explicit or inferred CLI flag, explicit or inferred config-option, or explicit, inferred, or natural-language environment-variable-backed feature edit
- perform safe multi-file renames
- support a diagnose-only path that gathers failure evidence without applying edits
- persist an explicit task plan with a chosen validation command before acting
- narrow feature and rename validation to matching test files when repo text or module structure makes the target clear, including nested repo-relative test paths
- carry a compact working-memory snapshot across resumed sessions
- rerun validation
- review and resume past sessions
- run a small fixed eval suite covering task success, natural-language bug-intent routing, natural-language feature requests, approval gating, and resume flow
- persist eval summaries as JSON artifacts with timestamps, labels, timing, and outcome reasons
- list saved eval artifacts by date, label, and pass rate
- resolve saved eval artifacts by label for compare and history workflows
- support aliases like `latest`, `latest-pass`, and `latest:<prefix>` for eval selection
- store named baselines like `main`, `release`, or `golden` for stable eval references
- promote a resolved artifact into a named baseline in one step
- compare a named baseline against `latest-pass` or another resolved reference in one step
- auto-promote a candidate into a baseline only when comparison shows no regressions
- compare saved eval artifacts to detect regressions and improvements
- persist comparison and auto-promotion decisions as JSON artifacts for later audit
- summarize scenario trends across multiple eval artifacts
- persist a session trail

As of Sunday, August 9, 2026, the current local test suite for `coding-agent-v1` is passing:

- `123 passed`

## Repository Layout

- `sources/pdfs/`: canonical source documents
- `sources/external/`: external repos and source mappings we want to track against
- `notes/`: cleaned markdown summaries and review notes
- `projects/`: concrete project briefs and checklists derived from the notes
- `evals/`: evaluation plans, task sets, and benchmark notes
- `docs/coding-agents/`: longer-form canonical writeups for the current focus area
- `docs/agent-evals/`: canonical writeups for tool use, multi-step traces, runtime checks, and complex-agent evaluation
- `docs/architecture-advances-2026/`: canonical writeups for long-context architecture efficiency ideas from `LLMArchitectureAdvances2026.pdf`
- `docs/qwen3-from-scratch/`: canonical writeups for the Qwen3 implementation track
- `projects/llm-developments-2026/`: project briefs for production experiments derived from `LLMDevelopments.pdf`
- `evals/llm-developments-2026/`: benchmark plans for retrieval, context pressure, verifier loops, and long-horizon CLI tasks
- `code/llm-developments-2026/`: the runnable experiment harness for those plans — retrieval/context/instruction/verifier/test-time-scaling sweeps, scorecards, and an auto-generated adoption memo (37 tests)
- `evals/agent-evals/`: benchmark plans, rubrics, dataset notes, and scenario-pack shape for the agent-evaluation track
- `code/qwen3-parity/`: implementation workspace for the reference-vs-scratch Qwen3 project

## Source Documents

The original PDFs currently live at the repo root. They should be treated as source artifacts.

Priority documents:

- `CodingAgents.pdf`
- `OpenCodingAgents.pdf`
- `LLMArchitectureAdvances2026.pdf`
- `sources/external/building-a-coding-agent-from-scratch-course/README.md`

Secondary documents:

- `LLMEvalApproaches.pdf`
- `InferenceTimeScaling.pdf`
- `LLMDevelopments.pdf`
- `LLmReasoning.pdf`
- `LLmArchitecture.pdf`
- `openweights.pdf`

## Initial Working Position

`CodingAgents.pdf` and `OpenCodingAgents.pdf` play different roles:

- `CodingAgents.pdf`: stable conceptual model for how a coding-agent harness should work
- `OpenCodingAgents.pdf`: practical local-stack setup reference for experiments with open-weight models and local harnesses

The external Decoding AI course adds a third layer:

- `building-a-coding-agent-from-scratch-course`: concrete from-scratch implementation map with real modules for tools, permissions, memory, runtime, sandboxing, evals, and subagents

The repo should therefore separate durable architecture notes from operational setup notes.

There is now also a separate agent-evaluation lane for turning the "how do we evaluate real agents?" question into concrete repo work around:

- tool-call grading
- multi-step trace debugging
- runtime safety checks
- document and multimodal agent evaluation

There is now also an `LLMDevelopments.pdf` implementation lane for turning broad 2026 paper trends into production-scale experiments around:

- retrieval strategy
- context assembly
- verifier loops
- long-horizon CLI workflows
- long-context systems prototypes

## Next Steps

1. Convert `OpenCodingAgents.pdf` into a second note focused on local stack decisions, risks, and evaluation criteria.
2. Flesh out `docs/architecture-advances-2026/`, `projects/architecture-advances-2026/`, and `evals/architecture-advances-2026/` into concrete prototype specs.
3. Convert `Qwen3fromscratch.pdf` into a durable implementation note and drive a Qwen3 0.6B parity project from it.
4. Build the new `docs/agent-evals/`, `projects/agent-evals/`, and `evals/agent-evals/` lane into runnable datasets, rubrics, and evaluators, with `projects/coding-agent-v1/` as the first integration target.
5. Extend the `code/llm-developments-2026/` harness: it now runs retrieval, context, instruction, verifier, and test-time-scaling sweeps with scorecards and an adoption memo; still owed are long-horizon multi-step CLI chains, retrieval reranking, async handoff artifacts, and promotion of the winning defaults into `projects/coding-agent-v1/`.
6. Normalize PDF naming and move source files under `sources/pdfs/` once references are updated.
7. Add an initial evaluation matrix for harnesses, models, permissions, and task success.
8. Use `projects/coding-agent-from-scratch-implementation-map.md` as the bridge from the PDF concepts to a real codebase structure.
9. Extend `projects/coding-agent-v1/` from single-bug repair into broader tasks like small feature work, safe renames, and richer session resume flows.
