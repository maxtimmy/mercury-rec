# Model Card — Ranking model

> Заполняется при первом кандидате на registry. Не утверждать model performance до завершения зафиксированной evaluation.

## Identity

| Field | Value |
|---|---|
| Model name/version | TBD |
| Role | Candidate ranker |
| Owner | TBD |
| Registry URI/run | TBD |
| Git SHA/config | TBD |
| Dataset/split version | TBD |

## Intended use

Ранжирование товарных кандидатов для персонализированной e-commerce выдачи. Не используется для ценообразования, кредитных/правовых решений или профилирования за пределами выбранных recommendation features.

## Inputs and outputs

- Input: point-in-time user, item и cross features для уже сформированного candidate set.
- Output: относительный score для сортировки внутри одного request/model version.
- Fallback: при отсутствии истории/зависимостей применяется documented popularity policy, а не случайный score.

## Training and evaluation

- Label/horizon: TBD.
- Negative sampling: TBD.
- Temporal boundaries: TBD.
- Primary metric/guardrails: TBD.
- Results and slices: TBD (ссылка на MLflow and `experiments.md`).

## Limitations and risks

- Historical purchases содержат exposure/popularity bias и не доказывают causal online lift.
- Sparse users и новые items имеют ограниченный personalization signal.
- Product metadata может быть неполной или изменённой во времени.
- Offline metrics могут ухудшиться в serving из-за freshness/skew/dependency degradation.

## Monitoring and rollback

Monitor score distribution, feature missingness, retrieval-source availability, latency and offline delayed quality proxy. Rollback: переключить registry alias `champion` на prior validated version and invalidate compatible model/index cache. Точный runbook: [operations.md](operations.md).
