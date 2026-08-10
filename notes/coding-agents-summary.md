# Coding Agents Summary

Source: `CodingAgents.pdf`  
Author: Sebastian Raschka  
Document date: April 4, 2026

## Why This Document Matters

This is the strongest first document in the collection because it is mostly about durable system design. Instead of centering on one vendor or one CLI, it explains the runtime structure that makes coding agents useful in practice.

The central claim is that a coding agent is not just a strong model. It is a model wrapped in an agent harness that manages context, tools, memory, execution, and control flow. For practical coding tasks, that harness can matter as much as the model itself.

## Core Distinctions

- LLM: the base next-token model
- Reasoning model: an LLM optimized to spend more inference-time compute on intermediate reasoning or verification
- Agent: a control loop around the model
- Agent harness: the software layer that manages prompts, tools, state, and execution
- Coding harness: an agent harness specialized for repository-aware software work

This distinction is useful for project planning because it prevents us from collapsing model quality and system quality into the same thing.

## Six Core Components

### 1. Live Repo Context

The agent should know where it is working before it acts. That includes repo root, branch, workspace layout, relevant instruction files, and current Git state.

Practical implication: a coding agent should build a workspace summary before starting work. Requests like "fix the tests" are underspecified without repo-specific context.

### 2. Prompt Shape and Cache Reuse

The document argues that a good harness separates stable prompt content from turn-specific content.

Stable content typically includes:

- general instructions
- tool descriptions
- workspace summary

Dynamic content typically includes:

- latest user request
- short-term memory
- recent transcript

Practical implication: any future project should explicitly model prompt prefixes and cache reuse instead of rebuilding one giant prompt every turn.

### 3. Structured Tools, Validation, and Permissions

The model should not improvise arbitrary action formats. The harness should expose named tools with bounded inputs, validate requests, gate risky actions, and restrict file access to the workspace where possible.

Validation questions called out in the document include:

- is this a known tool?
- are the arguments valid?
- does this need user approval?
- is the path inside the workspace?

Practical implication: tool schema and runtime policy are first-class architecture, not implementation detail.

### 4. Context Reduction and Output Management

Coding agents accumulate large file reads, logs, command output, and transcript history quickly. The document treats context management as a core quality lever.

Techniques emphasized:

- clipping long outputs
- compressing older transcript entries
- keeping recent events richer than older ones
- deduplicating repeated file reads

Practical implication: apparent model quality is often actually context quality.

### 5. Structured Session Memory

The document separates two different forms of state:

- working memory: small distilled state for continuity
- full transcript: durable record of user requests, tool calls, outputs, and model responses

Practical implication: storage-time state and prompt-time state should not be conflated. We should design both explicitly in any implementation project.

### 6. Delegation With Bounded Subagents

Subagents are useful for side quests such as locating symbols, checking config, or diagnosing failures while the main agent continues the primary task.

The key constraint is boundedness:

- enough inherited context to be useful
- limited recursion depth
- scoped task boundaries
- possibly read-only access depending on the harness

Practical implication: delegation is valuable, but unconstrained delegation creates duplication and coordination risk.

## What To Keep

These ideas look stable enough to treat as long-term design constraints:

- repo-aware workspace summaries
- prompt prefix separation
- structured tool interfaces
- explicit approval and path boundaries
- transcript compaction and deduplication
- durable session storage
- bounded subagent delegation

## What Not To Overfit

The PDF references current products such as Codex and Claude Code, but the main value is not product comparison. The value is the architecture pattern behind those tools.

We should avoid turning this note into a vendor comparison doc. That belongs in evals.

## Project Seeds From This Document

1. Build a coding-agent harness checklist for reviewing real tools.
2. Define a minimal reference architecture for an internal agent project.
3. Create an evaluation rubric for context management, permissions, and resumability.
4. Prototype a lightweight session-store format for transcript plus working memory.

## Open Questions For Follow-On Work

- What is the minimum useful workspace summary for a real repo?
- Which tool boundaries should be hard-coded versus policy-driven?
- How aggressive should transcript compaction be before correctness degrades?
- When should a subagent be read-only versus fully writable?
