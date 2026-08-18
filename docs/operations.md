# Operations: serving, monitoring, retraining

## SLOs и измерения

До benchmark это цели: P95 `< 100 ms`, service availability и error budget TBD. После V3 в этой секции фиксируются результаты и условия теста; не переносить target как achieved metric.

Prometheus metrics минимум:

- `recommendation_requests_total{status,fallback,model_version}`;
- `recommendation_request_duration_seconds` histogram;
- `recommendation_candidates_count{source}`;
- `feature_lookup_duration_seconds`, `feature_missing_total{feature}`;
- `model_load_failures_total`, `dependency_errors_total{dependency}`;
- consumer lag, processed/DLQ events, event-to-feature freshness.

Grafana dashboards: API health, retrieval/ranker timing, dependencies, stream lag/freshness, feature quality and model outputs. Alert rules должны иметь severity, owner, threshold, duration и runbook link.

## Drift and quality

Evidently запускается batch job-ом на reference window (training/validated serving) и current window. Monitored distributions: price, category, user activity, item popularity, missingness and prediction scores. Drift — повод для исследования, не автоматическое доказательство деградации качества.

Если delayed labels доступны из replay, считать rolling offline proxy; online CTR не заявлять без настоящего controlled experiment.

## Retraining flow

```text
schedule -> validate raw data -> build PIT features -> train -> evaluate
  -> compare champion -> register challenger -> approve/promote or reject -> report
```

Prefect flow является идемпотентным по `run_id`; каждый шаг публикует artifact/metadata. Promotion требует gate из [ml-and-evaluation.md](ml-and-evaluation.md). Автоматическое deployment допускается только в локальном demo environment; ручное approve — безопасный default.

## Incident response

1. Проверить dashboard, scope и затронутый `model_version`/feature version.
2. Mitigate: включить known-good fallback или rollback champion согласно runbook.
3. Сохранить evidence: timestamps, configs, logs, affected metrics.
4. Исправить contract/validation, добавить regression test и заполнить postmortem.

Первый учебный incident: `price` в EUR при training и в cents при serving. Expected detection: price drift, score distribution shift and/or feature range validation. Шаблон: [postmortem-001.md](postmortem-001.md).
