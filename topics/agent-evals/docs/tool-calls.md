# Evaluating Tool Calls

Tool use should be graded in four separate stages.

If we skip that split, one bad final answer can hide four different bugs.

## Stage 1: Tool selection

Question:

did the model choose the right tool?

Typical failures:

- picked the wrong tool
- failed to call a tool when it needed one
- hallucinated a tool that does not exist

What to check:

- the user request
- the available tool list
- the chosen tool
- the expected correct tool

Typical fixes:

- rewrite tool names
- sharpen tool descriptions
- reduce overlap between similar tools

## Stage 2: Argument generation

Question:

did the model produce arguments that are both valid and correct?

Two different checks live here:

1. structural validity
   - required fields exist
   - types are correct
   - formats are correct
2. semantic correctness
   - the values actually match the user request and system rules

Typical failures:

- wrong field type
- missing required field
- wrong identifier
- unsafe raw user input copied into a query

Typical fixes:

- tighter schemas
- validators
- enum constraints
- pre-execution safety checks

## Stage 3: Execution

Question:

did the tool run successfully in the real system?

Typical failures:

- network timeout
- missing resource
- permission error
- tool returns an empty result that is technically valid but practically wrong

This stage is not about model judgment.

It is about whether the external system actually worked.

Typical fixes:

- retries
- fallback behavior
- stronger error capture
- tool reliability work

## Stage 4: Output handling

Question:

did the model read the tool result correctly and use it correctly?

Typical failures:

- misread a field from the tool output
- ignored an important warning in the output
- asked the user for information the tool already returned
- gave a final answer that conflicts with the tool result

Typical fixes:

- better prompting around result handling
- explicit output post-processing
- output-grounding checks
- targeted judges for semantic consistency

## The rule

Every serious tool-using agent should log enough structure to answer:

1. which tool was chosen
2. what arguments were generated
3. what the tool returned
4. how the model used that return value

If one of those is missing from the trace, debugging gets much harder.
