# Coding Agent V1 Planner And Eval Upgrade

This file defines the next implementation milestone after `coding-agent-v1-foundation`.

It answers one practical question:

what should we build next inside `projects/coding-agent-v1/` now that the first foundation milestone is committed?

## Milestone Name

`coding-agent-v1-planner-and-eval-upgrade`

## Why This Is The Next Milestone

As of Sunday, August 9, 2026, the foundation milestone is already real:

- `projects/coding-agent-v1/` exists as a committed implementation artifact
- its local test suite is passing with `123 passed`
- the repo has a clean first milestone history for that harness

That means the next highest-leverage step is not packaging again.

The next highest-leverage step is improving agent quality in the two weakest V1 areas:

- planner quality
- eval coverage

Those are the places where the current harness is still visibly heuristic and narrow.

## Core Goal

Push `coding-agent-v1` beyond its current scored-evidence planner rules and narrow eval set so the repo can demonstrate a more evidence-based, more measurable coding agent.

## What Should Improve In This Milestone

This milestone should improve three things together.

### 1. Planner Quality

The current planner is useful, but still mostly a rule system with scored evidence.

This milestone should make planning better at:

- choosing among competing task strategies
- explaining why one strategy beat another
- handling feature work with clearer evidence
- avoiding weak validation choices when the workspace suggests better targets

### 2. Validation Selection

The current harness already narrows some validation commands using request text and module-aware test evidence.

This milestone should broaden that so feature and rename work can choose stronger validation commands more consistently.

### 3. Eval Coverage

The current eval support is real, but still too small to prove broad progress.

This milestone should expand evals so the planner and validation changes can be measured instead of described.

## Concrete Scope

This milestone should stay focused on quality improvements inside the existing V1 harness.

In scope:

- planner improvements inside `projects/coding-agent-v1/src/coding_agent_v1/planner.py`
- validation-selection improvements inside the current V1 flow
- additional eval scenarios and tests for planner and validation behavior
- updated docs that describe the stronger V1 behavior

Out of scope:

- full LLM integration
- subagents
- cloud runtime work
- distributed execution
- heavy sandbox redesign
- unrelated new research tracks

## Minimum Success Criteria

Treat this milestone as successful only if all of these are true.

### 1. Planner Decisions Are More Explicit

The planner should record stronger reasons when choosing:

- fix vs diagnose
- feature vs inspect
- targeted validation vs full-suite fallback

### 2. Validation Selection Is Broader

The harness should demonstrate stronger validation selection for at least:

- feature tasks beyond the simplest CLI-flag case
- rename tasks where multiple test candidates exist
- workspace layouts where request text is weak but module evidence is strong

### 3. Eval Coverage Expands

The eval suite should grow in a way that makes planner and validation improvements visible.

That means adding scenarios that probe:

- strategy selection quality
- validation-target choice
- fallback behavior when evidence is weak

### 4. The Improvement Is Test-Backed

The local V1 test suite should still pass after the upgrade.

This milestone should not rely on one-off examples alone.

## Recommended Build Order

The cleanest order for this milestone is:

1. tighten planner reasoning and recorded reasons
2. improve validation-target selection rules
3. add eval scenarios that prove the new behavior
4. add or update focused tests
5. update V1 docs to describe the stronger behavior

That order keeps behavior changes and measurement changes connected.

## Suggested Files To Expect Changes In

The highest-probability change areas are:

- `projects/coding-agent-v1/src/coding_agent_v1/planner.py`
- `projects/coding-agent-v1/src/coding_agent_v1/agent_loop.py`
- `projects/coding-agent-v1/src/coding_agent_v1/eval_harness.py`
- `projects/coding-agent-v1/tests/test_agent_loop.py`
- `projects/coding-agent-v1/tests/test_eval_harness.py`
- `projects/coding-agent-v1/README.md`

## Verification Path

At minimum, this milestone should be verified with:

```bash
cd /home/manishmehta/ui-projects/sebastian-llms/projects/coding-agent-v1
python3 -m pytest tests/test_agent_loop.py -q
python3 -m pytest tests/test_eval_harness.py -q
python3 -m pytest tests -q
```

If a dedicated milestone verifier becomes useful later, it can be added once this milestone has a stable boundary.

## What This Milestone Should Teach

This milestone should make one lesson clearer in the portfolio:

building the first agent harness is only step one; improving planner quality and measurement discipline is what turns it into a serious engineering system.

## Relationship To Later Milestones

This milestone should come before:

- stronger long-session memory work
- benchmark-lab expansion beyond V1
- flagship capstone packaging

That is because better planning and better evals are the shortest path to a visibly stronger agent.

## Bottom Line

The right next step after `coding-agent-v1-foundation` is not a new toy project.

It is a tighter, more measurable V1:

better planner choices, better validation choices, and broader eval coverage inside the harness we already built.
