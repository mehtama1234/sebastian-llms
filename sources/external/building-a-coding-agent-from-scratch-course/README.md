# Building a Coding Agent From Scratch Course

External source tracked for implementation reference.

## Source

- Repository: `https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course`
- Branch reviewed: `main`
- Remote `HEAD` at review time: `adf83be4200380e0771a7b8621b38b31e5e5e492`
- Review date: August 9, 2026

## Why It Matters Here

This repo is the concrete implementation companion to the ideas in `CodingAgents.pdf`.

In simple terms:

- `CodingAgents.pdf` explains what a coding-agent harness should contain
- this course repo shows one way to actually build those parts in code

## Key Implementation Areas

- `src/decode/agent/`: core loop, dependencies, context window, factory
- `src/decode/tools/`: tool registry and tool implementations
- `src/decode/permissions/`: modes, rule engine, gate
- `src/decode/context/`: compaction and session logs
- `src/decode/memory/`: memory extraction and file-backed memory
- `src/decode/runtime/`: durable execution flow
- `src/decode/sandbox/`: docker and modal sandbox backends
- `src/decode/skills/`: progressive-disclosure skill system
- `src/decode/agents/`: catalog of agent personas
- `src/decode/services/lsp/`: LSP integration
- `evals/`: benchmark, regression, and online eval harnesses
- `docs/adr/`: design decisions by milestone

## Useful Design Docs

- `docs/adr/0002-milestone-1-vanilla-agent-architecture.md`
- `docs/adr/0003-milestone-2-permission-system-and-agents-catalog.md`
- `docs/adr/0004-milestone-3-skills.md`

## Working Interpretation

This is not just a toy agent loop. It is a full harness-oriented implementation with:

- a thin agent loop
- a larger surrounding system
- explicit permissions
- session state
- context management
- skills
- subagents
- sandboxes
- evals

That matches the main claim from `CodingAgents.pdf`: the harness does most of the real work.
