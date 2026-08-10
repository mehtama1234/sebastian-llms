# Agent Evals Project Track

This project track turns the agent-evaluation topic into buildable repo work.

Canonical docs:

- `../../docs/agent-evals/README.md`
- `./meaty-end-to-end-goal.md`

## Goal

Build a reusable evaluation layer for tool-using and multi-step agents, then apply it to `projects/coding-agent-v1/` first.

## End state

This track is successful when the repo contains:

- one explicit trace schema for tool-using runs
- one stage-level evaluator for tool selection, arguments, execution, and output handling
- one end-to-end evaluator for task success and safety
- one runtime-check layer for high-risk actions
- one scenario catalog covering read tools, write tools, multi-step traces, and multimodal/document cases
- one first implementation wired into `projects/coding-agent-v1/`

## Working position

The point is not to create one more benchmark spreadsheet.

The point is to make agent failures diagnosable and fixable.

That means every bad run should move us toward an answer to:

- what failed
- where it failed
- whether it was safe
- what class of fix is needed
