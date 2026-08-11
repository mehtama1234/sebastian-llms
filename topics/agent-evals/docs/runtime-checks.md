# Runtime Checks

Offline evaluation has ground truth.

Production often does not.

That means a live agent needs cheap checks that can catch likely bad actions before damage happens.

## The basic split

There are two different evaluation moments:

1. `offline eval`
   - we already know the right answer
   - we compare the agent against ground truth
2. `runtime`
   - we do not know the true answer yet
   - we only know whether the action looks sufficiently grounded and safe

## Cheap runtime checks

Cheap checks are small tests that run before a high-risk action is allowed.

Text examples:

- did the tool call parse against schema?
- did a retrieval-backed answer cite the retrieved source?
- does the final claim contradict the tool output?
- did two independent reads of the same field agree?
- did the system ask for confirmation before an irreversible action?

Vision and document examples:

- did the model point to the exact region that supports the extracted value?
- does a second OCR pass match the extracted text?
- do subtotal, tax, and total add up?
- did the image/document parser actually return readable content?

## Escalation rule

Runtime checks need an action attached.

A check without an action is decoration.

Typical actions:

- allow automatically
- block automatically
- retry with another tool or prompt
- send to human review

## High-risk write tools

Write tools need stricter gating than read tools.

Examples:

- send email
- pay invoice
- delete file
- update database row
- cancel order

For these, the minimum standard should usually include:

- schema validation
- grounding evidence
- consistency check
- explicit confirmation or policy-based permission gate

## Working rule

If the system cannot prove enough about a high-risk action, the correct behavior is often:

stop and escalate.

A safe stop is a success condition, not a failure.
