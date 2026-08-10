# Coding Agent Harness Checklist

Derived from: `notes/coding-agents-summary.md`

Use this checklist to review existing coding agents or to scope a new implementation.

## Repo Context

- Detect repo root reliably.
- Capture branch, status, and recent commit context.
- Discover project instructions such as `README.md`, `AGENTS.md`, or equivalent.
- Build a compact workspace summary before task execution.

## Prompt Architecture

- Separate stable prompt prefix from per-turn state.
- Keep tool descriptions out of the frequently changing prompt region when possible.
- Track short-term memory separately from raw transcript history.
- Define an explicit policy for prompt cache invalidation.

## Tools and Runtime Safety

- Expose tools through a structured schema.
- Validate arguments before execution.
- Enforce workspace path boundaries.
- Gate risky actions through approval or policy.
- Bound command execution and output size.

## Context Management

- Clip large command outputs.
- Deduplicate repeated file reads.
- Compress older history more aggressively than recent history.
- Prevent single verbose tools from dominating the prompt budget.

## Memory and Resumption

- Store a full durable transcript.
- Maintain a smaller working-memory layer.
- Support resumable sessions.
- Distinguish storage-time state from prompt-time summary.

## Subagents

- Allow bounded delegation for focused subtasks.
- Limit recursion depth.
- Scope subagent permissions explicitly.
- Prevent overlapping writes without coordination.

## Evaluation Questions

- Does the harness stay accurate as context grows?
- Does it fail safely on invalid tool requests?
- Can it resume work cleanly after interruption?
- Does delegation reduce work or just duplicate it?
- Is token usage efficient relative to task success?
