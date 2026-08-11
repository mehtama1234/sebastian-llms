# Meaty End-to-End Goal

Build a real evaluation lab for tool-using agents, not just a loose set of agent demos.

The end product should be a small, owned, repeatable stack that can take an agent trace, grade each important stage, catch unsafe runtime actions, and tell us what actually broke when a run fails.

## What we are building

We want one place where we can:

- define golden tasks for tool use and agent behavior
- store full traces with enough structure to debug them
- evaluate single tool calls and multi-step traces separately
- measure both task success and safety
- add cheap runtime checks for cases where no immediate ground truth exists
- apply the same machinery first to `projects/coding-agent-v1/`

This is not "read about agent evaluation."

This is "turn agent evaluation ideas into datasets, rubrics, code hooks, and runnable checks."

## The concrete question

For each agent capability, we want to answer:

1. Did the agent choose the right action path?
2. Did it use the right tool with the right arguments?
3. Did the external tool actually succeed?
4. Did the model interpret the result correctly?
5. Did the full run safely achieve the user goal?
6. If it failed, where was the first real failure?

## The implementation target

The project is successful when the repo contains:

- one shared trace format for agent runs
- one scenario catalog with gold expectations
- one rubric layer for pass/fail and failure typing
- one stage-level evaluator for:
  - tool selection
  - argument generation
  - execution success
  - output handling
- one trace-level debugger based on first-failure attribution
- one runtime-check layer for high-risk writes and weakly grounded outputs
- one integration target inside `projects/coding-agent-v1/`

## What done means

Done means we can run a small but serious set of agent tasks and say, with artifacts:

- this failed at argument generation, not planning
- this failed because the write action was not sufficiently grounded
- this task succeeded end to end but the path was unreliable
- this runtime check correctly escalated a risky action instead of guessing

The point is to force failure attribution, not just collect pass rates.

## Why this matters

If this lands properly, it becomes the evaluation backbone for future agent work in the repo:

- coding agents
- retrieval agents
- document agents
- multimodal agents

That is the meaty end state:

an owned agent-evaluation harness, a clear scenario catalog, and a first real integration target that makes agent improvements measurable instead of vibes-based.
