# Multimodal And Document Inputs

Agents that read images, PDFs, or long documents have one extra failure boundary:

bad input processing can look like bad reasoning.

We have to separate them.

## Images

Main questions:

- did the words match the image?
- did the model hallucinate objects or text?
- did it count or locate things correctly?
- was the answer grounded in the actual pixels?

Useful checks:

- image-to-answer consistency
- swap-image sensitivity
- blur/occlusion robustness
- refusal when the image is unreadable

## PDFs and OCR

The common trap:

the LLM gets blamed for a bad extraction pipeline.

Before judging reasoning, inspect:

- the extracted text
- the reading order
- table formatting
- OCR quality

If the extracted content is broken, that is an ingestion problem first.

## Long documents

Two main task shapes matter:

1. constant-size output
   - find one small fact in a long context
2. variable-size output
   - extract or summarize many things across the whole document

These need different evaluation styles.

Constant-size tasks care about:

- whether the model can find the right needle
- whether middle-of-context performance collapses

Variable-size tasks care about:

- chunking strategy
- chunk-level precision and recall
- aggregation quality across chunks

## Practical rule

For multimodal or document-heavy agents, always ask two separate questions:

1. was the input representation good?
2. given that representation, was the reasoning good?

That split prevents wasted model work when the real bug is upstream parsing.
