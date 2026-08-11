# Agent Evals Scenario Packs

This folder should hold runnable scenario packs for tool-using agents.

## Current files

- `schema-v1.json`
  - JSON schema for the richer scenario-pack format
- `coding-agent-v1-smoke-v1.json`
  - first extended pack built around the existing `coding-agent-v1` smoke scenarios

## First pack families

- `smoke`
  - tiny pack that touches each core failure boundary once
- `core`
  - balanced pack across read tools, write tools, and multi-step flows
- `stress`
  - ambiguous, long-horizon, and safety-sensitive tasks

## Scenario fields to require

- `id`
- `task_class`
- `user_request`
- `available_tools`
- `expected_outcome`
- `safety_rules`
- `expected_tool_sequence`
- `expected_escalation_behavior`
- `failure_labels_if_broken`

## First integration target

These packs should be shaped so `projects/coding-agent-v1/` can eventually execute them without a full redesign.

The current `coding-agent-v1-smoke-v1.json` follows that rule by preserving the existing external-pack fields while adding richer expectations for:

- available tools
- expected tool sequence
- escalation behavior
- likely first-failure states
- trace requirements
