# Experiments and benchmarks

## Правила

- Один experiment row = immutable config, git SHA, dataset version, split ID, seed и artifact URI.
- Результаты не округляются так, чтобы скрыть variance; при возможности приводится confidence interval/bootstrap.
- Сравнение честно только при одном evaluation protocol.
- Цели не записываются как фактические значения.

## Experiment ledger

| ID | Date | Model | Candidate sources/budget | Feature set | Split | NDCG@10 | Recall@50 | P95 | Status |
|---|---|---|---|---|---|---:|---:|---:|---|
| EXP-001 | 2026-08-18 | Global popularity | popularity / 50 | none | test 2020-09-16 | 0.01449 | 0.07294 | — | measured baseline |
| EXP-002 | 2026-08-18 | ALS | ALS / 50 | none | test 2020-09-16 | 0.01231 | 0.03639 | — | measured retrieval source |
| EXP-003 | 2026-08-19 | Item-item co-occurrence | co-occurrence / 50 | 90d, latest 20 items | test 2020-09-16 | 0.00599 | 0.03369 | — | measured retrieval source |
| EXP-004 | 2026-08-19 | LambdaMART | popularity + ALS + item-item / 50 each | point-in-time user/item/affinity | test 2020-09-16 | 0.02298 | 0.08484 | — | challenger |

## Cost/latency decision record

После V3 заполнить реальными результатами:

| Serving variant | Candidate budget | NDCG@10 | P50/P95/P99 | RPS | CPU/memory | Decision |
|---|---:|---:|---|---:|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD |

Отдельно зафиксировать hardware, concurrency, cache state, duration, request mix и dataset/model version. Решение вроде «500 → 100 candidates» принимается только по этой таблице и описывается в ADR.
