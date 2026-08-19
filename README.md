# MercuryRec — Real-Time Personalized Recommendation Platform

MercuryRec — портфолио-проект production-minded рекомендательной системы для e-commerce. Система формирует персональный топ товаров по запросу API и демонстрирует полный ML lifecycle: события, point-in-time признаки, retrieval, ranking, serving, мониторинг и controlled retraining.

> Статус: V1 — измеренный offline baseline; V2 — измеренный offline challenger с two-stage LambdaMART. Champion пока не назначен, поскольку serving и online evaluation ещё не реализованы. Целевые SLO остаются гипотезами до измерений.

## Задача

По `user_id` вернуть до `limit` релевантных товаров:

```http
GET /v1/recommendations/{user_id}?limit=20
```

Датасет: H&M Personalized Fashion Recommendations. Исторические транзакции используются для offline обучения и могут replay-иться в event stream.

## Архитектура

```text
Historical data ──> batch features ──> offline store ──> training ──> MLflow Registry
                                          │                              │
User events ──> Redpanda ──> stream features ──> Redis/Feast online ────┤
                                                                         v
Client ─────────────────────────────────────────────> FastAPI ─> Retrieval ─> Ranker ─> rules ─> response
                                                          │                       │
                                                          └──── Prometheus ───────┘
```

Подробности: [architecture.md](docs/architecture.md).

## План поставки

| Версия | Результат | Критерий готовности |
|---|---|---|
| V1 | Popularity + ALS и temporal evaluation | Измеренный воспроизводимый baseline без leakage |
| V2 | Multi-source candidates + LightGBM ranker | Измеренный offline challenger; нет online champion decision |
| V3 | FastAPI, Redis, Docker, load test | Измерены P50/P95/P99, RPS и error rate |
| V4 | Feast, MLflow, retraining pipeline | Единые feature definitions, model lineage и quality gate |
| V5 | Redpanda event replay и свежие online features | Задокументирована задержка propagation события |
| V6 | Monitoring, alerting, incident simulation | Есть dashboard, alert и postmortem |
| V7 | ADR, CI, integration/load tests, system-design polish | Все решения и компромиссы воспроизводимы |

Полный backlog и acceptance criteria: [implementation-plan.md](docs/implementation-plan.md).

## Документация

- [Архитектура](docs/architecture.md)
- [Датасет и provenance](docs/dataset.md)
- [Результаты benchmark-ов](docs/benchmarks.md)
- [Данные и feature contracts](docs/data-and-features.md)
- [API contract](docs/api.md)
- [ML-подход и evaluation](docs/ml-and-evaluation.md)
- [Model card](docs/model-card.md)
- [Эксперименты и benchmarks](docs/experiments.md)
- [Operations: serving, monitoring, retraining](docs/operations.md)
- [ADR](docs/architecture_decisions/README.md)
- [Шаблон postmortem](docs/postmortem-001.md)

## Принципы

- Только temporal splits; случайный `train_test_split` для финальной оценки запрещён.
- Любой feature на времени `T` строится только из событий раньше `T`.
- Baseline обязателен; новая модель сравнивается с текущим champion.
- Offline-метрики не интерпретируются как online business impact.
- Факт production-like не равен production: все ограничения и симуляции фиксируются честно.

## Предлагаемая структура кода

```text
src/{ingestion,features,retrieval,ranking,evaluation,serving}/
pipelines/
feature_store/
configs/
monitoring/{prometheus,grafana}/
tests/{unit,integration,load}/
infra/
notebooks/
docs/
```

## Запуск offline benchmark-ов

Положите Kaggle token в `~/.kaggle/kaggle.json`, затем подготовьте данные и запустите baseline:

```bash
make data-download
make data-validate
make train-baseline
```

После V1 запустите V2 candidate ablation и LambdaMART ranker:

```bash
make train-v2
```

Агрегированные V2 test-метрики и offline challenger decision опубликованы в [benchmarks.md](docs/benchmarks.md). Данные, token, ML artifacts и пользовательские предсказания намеренно не попадают в Git.
