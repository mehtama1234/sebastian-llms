# Compressed Attention Training Diagnosis

_Updated: 2026-08-09_

## Worst Loss Rows

| Batch | Seq Len | Steps | Seed | Loss Delta | Speed Ratio |
|---:|---:|---:|---:|---:|---:|
| 2 | 16 | 8 | 17 | 0.219 | 1.044 |
| 2 | 8 | 4 | 17 | 0.000 | 1.000 |
| 2 | 8 | 4 | 23 | 0.000 | 1.000 |

## Slowest Rows

| Batch | Seq Len | Steps | Seed | Loss Delta | Speed Ratio |
|---:|---:|---:|---:|---:|---:|
| 4 | 16 | 8 | 23 | -0.152 | 2.228 |
| 4 | 16 | 4 | 17 | -2.028 | 1.254 |
| 2 | 16 | 8 | 17 | 0.219 | 1.044 |

## Batch-size slices

| Batch Size | Rows | Mean Loss Delta | Worst Loss Delta | Mean Speed Ratio | Worst Speed Ratio |
|---:|---:|---:|---:|---:|---:|
| 2 | 8 | -0.840 | 0.219 | 0.969 | 1.044 |
| 4 | 8 | -0.551 | 0.000 | 1.119 | 2.228 |

## Sequence-length slices

| Seq Len | Rows | Mean Loss Delta | Worst Loss Delta | Mean Speed Ratio | Worst Speed Ratio |
|---:|---:|---:|---:|---:|---:|
| 8 | 8 | 0.000 | 0.000 | 1.000 | 1.000 |
| 16 | 8 | -1.391 | 0.219 | 1.089 | 2.228 |

## Step-count slices

| Steps | Rows | Mean Loss Delta | Worst Loss Delta | Mean Speed Ratio | Worst Speed Ratio |
|---:|---:|---:|---:|---:|---:|
| 4 | 8 | -1.137 | 0.000 | 1.016 | 1.254 |
| 8 | 8 | -0.254 | 0.219 | 1.073 | 2.228 |
