# Coding Agent From Scratch Implementation Map

This file connects the theory in `CodingAgents.pdf` to the practical structure in the Decoding AI course repo.

## Core Mapping

### 1. Live Repo Context

PDF idea:

- the agent should understand where it is working

Implementation direction:

- `src/decode/agent/deps.py`
- `src/decode/cli.py`
- `src/decode/tools/files.py`
- `src/decode/context/session_log.py`

### 2. Prompt Shape and Cache Reuse

PDF idea:

- stable prompt parts should be separated from changing state

Implementation direction:

- `src/decode/agent/factory.py`
- `src/decode/agent/context_window.py`
- `src/decode/context/compaction.py`
- `src/decode/memory/service.py`

### 3. Structured Tools, Validation, and Permissions

PDF idea:

- tools should be named, validated, and policy-bounded

Implementation direction:

- `src/decode/tools/registry.py`
- `src/decode/tools/files.py`
- `src/decode/tools/bash.py`
- `src/decode/permissions/gate.py`
- `src/decode/permissions/rules.py`
- `src/decode/entities/permissions.py`

### 4. Context Reduction and Output Management

PDF idea:

- the harness must avoid prompt bloat

Implementation direction:

- `src/decode/context/compaction.py`
- `src/decode/tools/truncate.py`
- `src/decode/agent/context_window.py`

### 5. Structured Session Memory

PDF idea:

- keep working memory and full transcript separately

Implementation direction:

- `src/decode/memory/`
- `src/decode/context/session_log.py`
- `src/decode/runtime/flow.py`

### 6. Delegation With Bounded Subagents

PDF idea:

- subagents are useful if they inherit enough context but stay bounded

Implementation direction:

- `src/decode/tools/agent.py`
- `src/decode/tools/orchestration.py`
- `src/decode/agents/`
- `docs/adr/0017-resilient-parallel-subagent-fanout.md`

## Suggested Build Order For Our Own Work

### V1

- basic loop
- repo-aware file tools
- bash tool with strict limits
- explicit permission gate
- simple session log

### V2

- mode switching
- agent catalog
- prompt compaction
- working memory

### V3

- skills
- LSP
- eval harness

### V4

- sandboxing
- durable runtime
- subagents
- parallel fan-out

## Recommended Reading Order

1. `notes/coding-agents-summary.md`
2. `notes/building-a-coding-agent-from-scratch-course-summary.md`
3. `projects/coding-agent-harness-checklist.md`
4. `projects/coding-agent-from-scratch-implementation-map.md`

## Bottom Line

The PDF tells us what a coding agent needs.

The course repo tells us how one serious implementation organizes those needs in code.

That is the bridge we should use for future projects in this folder.
