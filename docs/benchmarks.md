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

## V2 — two-stage ranker

Run `v2-20260819T065447Z` used the same 31,788,324-transaction snapshot and final test horizon (cutoff 2020-09-16; labels through 2020-09-22). Candidate sources were limited to 50 items each; co-occurrence used the prior 90 days and at most 20 recent distinct items per user. The local artifact, model and predictions remain ignored by Git.

| Candidate/ranker | Recall@10 | NDCG@10 | MRR@10 | Recall@50 | Coverage@50 | Novelty@50 | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Trending popularity | 0.02221 | 0.01449 | 0.01807 | 0.07294 | 0.00047 | 9.25772 | baseline |
| ALS | 0.01703 | 0.01231 | 0.01734 | 0.03639 | 0.01810 | 13.80830 | retrieval source |
| Item-item co-occurrence | 0.00923 | 0.00599 | 0.00888 | 0.03369 | 0.16357 | 12.35797 | retrieval source |
| Candidate union | 0.02220 | 0.01347 | 0.01700 | 0.06483 | 0.09577 | 11.36198 | retrieval ablation |
| LambdaMART ranker | 0.03059 | 0.02298 | 0.03319 | 0.08484 | 0.08527 | 9.91964 | challenger |

LambdaMART improves NDCG@10 by 58.6% relative to the best V1 baseline (0.02298 vs 0.01449). It also improves all release guardrails relative to popularity: Recall@50 (+16.3%), Coverage@50 and Novelty@50 (+7.1%). It therefore passes the challenger gate, but is **not** an online champion: no serving or online experiment exists yet.

Performance on the local benchmark host: validation feature generation 348.57s, ranker training 47.32s, test feature generation 346.70s, ranker inference 20.91s, serialized model 359,527 bytes, peak RSS 9,470 MiB. The normalized snapshot had zero nulls, a 9.36% exact-duplicate rate, 1,362,281 users and 104,547 items. The current diversity statistic verifies within-list deduplication; category-level diversity remains a future business-rule metric.
