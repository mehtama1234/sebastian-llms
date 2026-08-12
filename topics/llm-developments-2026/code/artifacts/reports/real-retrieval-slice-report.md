# Real Retrieval Slice Report

## all

- Recommended: `real_retrieval_lexical`
- Task count: `15`

| Policy | Accepted | Grounded | Gold-Hit Tasks | Mean Gold Recall | Tokens / Accepted Task |
|---|---:|---:|---:|---:|---:|
| `real_retrieval_lexical` | 0.933 | 1.000 | 0.933 | 0.628 | 406.8 |
| `real_retrieval_sparse` | 0.867 | 1.000 | 0.867 | 0.528 | 407.8 |
| `real_retrieval_task_aware` | 0.733 | 1.000 | 0.733 | 0.578 | 412.5 |

## long_context

- Recommended: `real_retrieval_sparse`
- Task count: `7`

| Policy | Accepted | Grounded | Gold-Hit Tasks | Mean Gold Recall | Tokens / Accepted Task |
|---|---:|---:|---:|---:|---:|
| `real_retrieval_lexical` | 1.000 | 1.000 | 1.000 | 0.560 | 431.7 |
| `real_retrieval_sparse` | 1.000 | 1.000 | 1.000 | 0.560 | 385.0 |
| `real_retrieval_task_aware` | 0.714 | 1.000 | 0.714 | 0.476 | 495.6 |

## short_context

- Recommended: `real_retrieval_lexical`
- Task count: `8`

| Policy | Accepted | Grounded | Gold-Hit Tasks | Mean Gold Recall | Tokens / Accepted Task |
|---|---:|---:|---:|---:|---:|
| `real_retrieval_lexical` | 0.875 | 1.000 | 0.875 | 0.688 | 381.9 |
| `real_retrieval_sparse` | 0.750 | 1.000 | 0.750 | 0.500 | 434.5 |
| `real_retrieval_task_aware` | 0.750 | 1.000 | 0.750 | 0.667 | 343.2 |

## inspect

- Recommended: `real_retrieval_lexical`
- Task count: `5`

| Policy | Accepted | Grounded | Gold-Hit Tasks | Mean Gold Recall | Tokens / Accepted Task |
|---|---:|---:|---:|---:|---:|
| `real_retrieval_lexical` | 1.000 | 1.000 | 1.000 | 0.517 | 385.2 |
| `real_retrieval_sparse` | 1.000 | 1.000 | 1.000 | 0.517 | 391.4 |
| `real_retrieval_task_aware` | 0.600 | 1.000 | 0.600 | 0.367 | 588.0 |

## diagnose

- Recommended: `real_retrieval_task_aware`
- Task count: `5`

| Policy | Accepted | Grounded | Gold-Hit Tasks | Mean Gold Recall | Tokens / Accepted Task |
|---|---:|---:|---:|---:|---:|
| `real_retrieval_lexical` | 0.800 | 1.000 | 0.800 | 0.600 | 477.0 |
| `real_retrieval_sparse` | 0.600 | 1.000 | 0.600 | 0.400 | 619.0 |
| `real_retrieval_task_aware` | 0.800 | 1.000 | 0.800 | 0.667 | 348.8 |

## bug_fix

- Recommended: `real_retrieval_sparse`
- Task count: `2`

| Policy | Accepted | Grounded | Gold-Hit Tasks | Mean Gold Recall | Tokens / Accepted Task |
|---|---:|---:|---:|---:|---:|
| `real_retrieval_lexical` | 1.000 | 1.000 | 1.000 | 1.000 | 230.0 |
| `real_retrieval_sparse` | 1.000 | 1.000 | 1.000 | 0.750 | 207.0 |
| `real_retrieval_task_aware` | 1.000 | 1.000 | 1.000 | 1.000 | 230.0 |

## research

- Recommended: `real_retrieval_sparse`
- Task count: `3`

| Policy | Accepted | Grounded | Gold-Hit Tasks | Mean Gold Recall | Tokens / Accepted Task |
|---|---:|---:|---:|---:|---:|
| `real_retrieval_lexical` | 1.000 | 1.000 | 1.000 | 0.611 | 467.0 |
| `real_retrieval_sparse` | 1.000 | 1.000 | 1.000 | 0.611 | 358.0 |
| `real_retrieval_task_aware` | 0.667 | 1.000 | 0.667 | 0.500 | 459.0 |
