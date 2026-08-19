# Model Card — Ranking model

> Offline challenger; не registry champion и не доказательство online impact.

## Identity

| Field | Value |
|---|---|
| Model name/version | `v2-20260819T065447Z` LambdaMART |
| Role | Candidate ranker |
| Owner | MercuryRec contributors |
| Registry URI/run | Not registered; local artifact only |
| Git SHA/config | `configs/v2-two-stage.yaml`, seed 42 |
| Dataset/split version | H&M snapshot 1c62791bac6a; validation cutoff 2020-09-09, test cutoff 2020-09-16 |

## Intended use

Ранжирование товарных кандидатов для персонализированной e-commerce выдачи. Не используется для ценообразования, кредитных/правовых решений или профилирования за пределами выбранных recommendation features.

## Inputs and outputs

- Input: point-in-time user, item и cross features для уже сформированного candidate set.
- Output: относительный score для сортировки внутри одного request/model version.
- Fallback: при отсутствии истории/зависимостей применяется documented popularity policy, а не случайный score.

## Training and evaluation

- Label/horizon: purchase in the following 7-day horizon.
- Negative sampling: non-purchased items already present in the point-in-time candidate pool.
- Temporal boundaries: validation 2020-09-09–2020-09-15; test 2020-09-16–2020-09-22.
- Primary metric/guardrails: NDCG@10; Recall@50, Coverage@50 and Novelty@50.
- Results: NDCG@10 0.02298, Recall@50 0.08484; passes the offline challenger gate. Full aggregate ablation: [benchmarks.md](benchmarks.md).

## Limitations and risks

- Historical purchases содержат exposure/popularity bias и не доказывают causal online lift.
- Sparse users и новые items имеют ограниченный personalization signal.
- Product metadata может быть неполной или изменённой во времени.
- Offline metrics могут ухудшиться в serving из-за freshness/skew/dependency degradation.

## Monitoring and rollback

Monitor score distribution, feature missingness, retrieval-source availability, latency and offline delayed quality proxy. Rollback: переключить registry alias `champion` на prior validated version and invalidate compatible model/index cache. Точный runbook: [operations.md](operations.md).
