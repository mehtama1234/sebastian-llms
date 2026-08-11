# Debugging Multi-Step Traces

A multi-step agent should not be judged only by the final answer.

When an end result is wrong, the real question is:

where did the run first become wrong?

## First-failure rule

Always try to find the first state where the trace violated a real criterion.

Do not blame the last visible failure by default.

Why:

errors cascade.

If step 2 was wrong, step 7 may look ridiculous even though it was only following bad input.

## Minimum trace record

For each step, keep:

- user input or current subgoal
- model reasoning summary or plan state
- chosen tool
- generated arguments
- tool response
- post-tool interpretation
- final action or next step

Without this, trace review turns into guesswork.

## State model

A practical first state breakdown is:

1. parse request
2. decide next action
3. generate tool arguments
4. execute tool
5. handle tool output
6. update plan
7. finish or escalate

That is enough to start counting where failures begin.

## Heatmap idea

Across many failed runs, count:

- the last good state
- the state where the first real failure happened

This produces a transition-failure heatmap.

Example:

- many failures from `generate arguments -> execute tool`
  - likely argument quality or missing tool constraints
- many failures from `handle tool output -> update plan`
  - likely interpretation or planning bugs

The point is not pretty analytics.

The point is to know what subsystem to fix first.

## Outcome still matters

Trace-level debugging does not replace end-to-end evaluation.

You still need to know:

- did the task succeed?
- was the action safe?
- did the system stop when it should have stopped?

Good trace analysis explains bad outcomes.
It does not replace them.
