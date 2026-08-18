# Experiments and benchmarks

## Правила

- Один experiment row = immutable config, git SHA, dataset version, split ID, seed и artifact URI.
- Результаты не округляются так, чтобы скрыть variance; при возможности приводится confidence interval/bootstrap.
- Сравнение честно только при одном evaluation protocol.
- Цели не записываются как фактические значения.

## Experiment ledger

| ID | Date | Model | Candidate sources/budget | Feature set | Split | NDCG@10 | Recall@50 | P95 | Status |
|---|---|---|---|---|---|---:|---:|---:|---|
| EXP-001 | — | Global popularity | popularity / 50 | none | TBD | TBD | TBD | TBD | planned |
| EXP-002 | — | ALS | ALS / 200 | none | TBD | TBD | TBD | TBD | planned |
| EXP-003 | — | Two-tower | mixed / 200 | retrieval features | TBD | TBD | TBD | TBD | planned |
| EXP-004 | — | Two-tower + LambdaMART | mixed / 200 | v1 PIT | TBD | TBD | TBD | TBD | planned |

## Cost/latency decision record

После V3 заполнить реальными результатами:

| Serving variant | Candidate budget | NDCG@10 | P50/P95/P99 | RPS | CPU/memory | Decision |
|---|---:|---:|---|---:|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD |

Отдельно зафиксировать hardware, concurrency, cache state, duration, request mix и dataset/model version. Решение вроде «500 → 100 candidates» принимается только по этой таблице и описывается в ADR.
