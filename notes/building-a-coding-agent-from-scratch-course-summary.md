# Building a Coding Agent From Scratch Course Summary

Source repo: `https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course`  
Reviewed branch: `main`  
Reviewed `HEAD`: `adf83be4200380e0771a7b8621b38b31e5e5e492`  
Review date: August 9, 2026

## What This Repo Is Saying

The repo makes a very direct claim: the agent itself is small, and the harness around it is where most of the value lives.

That is closely aligned with `CodingAgents.pdf`.

The implementation splits into two layers:

- a small model-driven loop
- a much larger harness containing tools, permissions, memory, runtime, sandboxing, skills, evals, and subagents

## Why This Matters For Our Folder

This gives us the practical counterpart to the PDF theory.

- `CodingAgents.pdf` gives us the conceptual architecture
- this course repo gives us an implementation reference

Together, they form a better starting base for launching our own coding-agent projects.

## Practical Implementation Shape

The codebase is organized in a clean way around major harness concerns:

- `src/decode/agent/`: loop and core dependencies
- `src/decode/tools/`: file, bash, web, orchestration, approval, tasks, LSP, skills
- `src/decode/permissions/`: permission modes and rules
- `src/decode/context/`: transcript/session compaction
- `src/decode/memory/`: working memory support
- `src/decode/runtime/`: durable and replayable execution path
- `src/decode/sandbox/`: execution isolation
- `src/decode/skills/`: progressive-disclosure instructions
- `src/decode/agents/`: agent catalog and persona selection
- `src/decode/services/lsp/`: editor-style code intelligence
- `evals/`: benchmark and regression system

## What It Is Proposing

This repo does propose a real implementation, not just ideas.

The implementation path is staged in milestones:

1. a vanilla coding agent loop
2. a permission system plus agent catalog
3. a skills system for progressive disclosure
4. later additions such as compaction, runtime durability, sandboxing, evals, and subagents

The ADRs make those milestone decisions explicit, which is useful because we can follow their reasoning instead of guessing why the structure exists.

## Best Takeaways

- Keep the core loop small.
- Treat permissions as architecture, not as a bolt-on.
- Separate agent personas from tool definitions.
- Use skills to avoid bloating the always-on prompt.
- Treat context compaction and memory as core runtime features.
- Build evals into the harness instead of adding them at the end.

## Differences From The PDF

`CodingAgents.pdf` is mostly architecture explanation.

This repo is an opinionated implementation of that architecture using:

- Python
- Pydantic AI
- a TUI
- explicit permission modes
- sandbox backends
- a benchmark and regression harness

So the repo is narrower than the PDF, but much more actionable.

## How We Should Use It

We should treat this repo as a reference implementation, not as something to copy blindly.

The most reusable ideas are:

- folder/module boundaries
- milestone sequencing
- ADR-style decision records
- eval-first thinking
- keeping the harness modular

## Recommended Follow-On Work

1. Use this repo to create our own implementation roadmap.
2. Map its modules back to the six components from `CodingAgents.pdf`.
3. Decide which parts are minimum viable for our own v1.
4. Keep sandboxing, runtime durability, and evals as later phases unless we need them immediately.
