# Benchmarks

This file contains only reproducible, measured results. Dataset archives, per-user predictions and MLflow artifacts remain local.

## V1 — offline baselines

| Run ID | Dataset checksum | Split | Model | Recall@10 | NDCG@10 | MRR@10 | Coverage@50 | Novelty@50 | Status |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| `baseline-20260818T113157Z` | `7ebd2532490f` | test: cutoff 2020-09-16, labels 2020-09-16–2020-09-22 | Trending popularity | 0.02221 | 0.01449 | 0.01807 | 0.00047 | 9.25772 | measured |
| `baseline-20260818T113157Z` | `7ebd2532490f` | test: cutoff 2020-09-16, labels 2020-09-16–2020-09-22 | Implicit ALS | 0.01703 | 0.01231 | 0.01734 | 0.01810 | 13.80830 | measured |

Dataset snapshot: 31,788,324 transactions from 2018-09-20 through 2020-09-22; 68,984 target users in the test horizon. The artifact itself is local and ignored by Git.

## Interpretation

ALS improved catalog coverage and novelty substantially, but the simpler popularity baseline performed better on test Recall@10 and NDCG@10. Therefore V1 does **not** promote ALS as a champion. This is the intended baseline for V2 candidate-source ablations and a ranker, rather than a reason to hide the result.

Run `make train-baseline` after downloading the dataset. Copy measured aggregate results from the local artifact to this table together with the run ID and dataset checksum; never publish raw customer-level outputs.
