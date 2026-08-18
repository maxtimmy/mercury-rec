# Benchmarks

This file contains only reproducible, measured results. Dataset archives, per-user predictions and MLflow artifacts remain local.

## V1 — offline baselines

| Run ID | Dataset checksum | Split | Model | Recall@10 | NDCG@10 | MRR@10 | Coverage@50 | Novelty@50 | Status |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| TBD | TBD | 7-day temporal | Trending popularity | TBD | TBD | TBD | TBD | TBD | planned |
| TBD | TBD | 7-day temporal | Implicit ALS | TBD | TBD | TBD | TBD | TBD | planned |

Run `make train-baseline` after downloading the dataset. Copy measured aggregate results from the local artifact to this table together with the run ID and dataset checksum; never publish raw customer-level outputs.
