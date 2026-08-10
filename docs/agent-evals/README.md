# Agent Evals

Canonical topic folder for evaluating tool use, multi-step agents, and runtime checks.

Primary source basis:

- `Evals for AI Engineers`, especially the material on multi-turn conversations, retrieval, tool use, and complex agents
- the coding-agent implementation and eval work already living in this repo

## Scope

This topic is about how to evaluate systems that do more than answer one prompt.

That includes:

1. tool-calling systems
2. multi-turn conversations
3. retrieval and document-grounded systems
4. agents that take actions in the world
5. multimodal agents that read images, PDFs, or long documents

The core move is simple:

do not grade only the final answer.

For agents, we must also grade:

- the intermediate decisions
- the tool arguments
- the execution outcomes
- the handoff from tool output back into model reasoning

## Why this matters

A complex agent can fail even when the final answer looks fine.

Examples:

- it chose the wrong tool
- it generated invalid or unsafe arguments
- the tool silently failed
- the model misread a correct tool result
- an early mistake cascaded through the rest of the trace
- the agent took an unsafe write action when it should have asked for confirmation

If we only score the final answer, those failures get mixed together and we do not know what to fix.

## Core evaluation frame

This topic breaks the problem into five layers:

1. `single step`
   - was one tool call correct?
2. `trace`
   - where in the multi-step run did the first real failure happen?
3. `outcome`
   - did the system change the world in the right way?
4. `runtime guard`
   - what cheap checks can stop bad actions when no ground truth exists yet?
5. `modality-specific input`
   - was the failure caused by bad image/document extraction or by bad reasoning?

## Folder map

- [tool-calls.md](./tool-calls.md): the four-stage model for evaluating tool use
- [multi-step-traces.md](./multi-step-traces.md): how to debug long agent traces and find the first failure
- [runtime-checks.md](./runtime-checks.md): cheap checks, escalation rules, and high-risk action gates
- [multimodal-and-doc-inputs.md](./multimodal-and-doc-inputs.md): images, PDFs, and long-document-specific eval issues

## Working position

This topic should become an implementation track, not just a note set.

The repo already has one strong execution target:

- `projects/coding-agent-v1/`

So the first practical use of this topic is:

build an eval layer that can grade `coding-agent-v1` and future agents at the tool-call, trace, and end-to-end outcome levels.
