# Архитектура

## Контекст и границы

MercuryRec — локально разворачиваемая демонстрационная recommendation platform, а не интернет-магазин и не доказательство online CTR uplift. H&M transactions выступают как batch history и replay source событий.

## Request path

1. API валидирует запрос, определяет cold/warm user и получает online features.
2. Retrieval объединяет до заданного бюджета кандидатов из popularity, CF и embedding ANN.
3. Ranker оценивает пары `(user, item)` point-in-time features.
4. Post-ranking rules отфильтровывают недоступные/дублирующиеся товары, применяют diversity и fallback.
5. API возвращает результаты с `model_version`, `request_id` и latency metadata; метрики и события логируются.

**Latency budget (гипотеза, до измерений):** feature lookup 10 ms, retrieval 25 ms, ranking 35 ms, rules/serialization 10 ms, запас 20 ms. Целевой P95 — менее 100 ms на согласованном hardware.

## Training path

```text
raw parquet -> validation -> point-in-time feature build -> candidate snapshots
     -> train retrieval/ranker -> offline evaluation -> MLflow run
     -> registry challenger -> quality gate -> champion
```

Все timestamps приводятся к UTC. Для каждой training row записываются `label_time`, feature cutoff и snapshot/index version.

## Компоненты

| Компонент | Назначение | Локальный выбор |
|---|---|---|
| Postgres/Parquet | raw/offline данные | Postgres + Parquet |
| Feast | единые feature definitions | Postgres/Parquet offline, Redis online |
| Redis | online features и краткоживущие state | Redis |
| Redpanda | event stream/replay | Kafka-compatible Redpanda |
| Retrieval | candidate set | ALS/BPR, two-tower, FAISS |
| Ranking | top-N scoring | LightGBM LambdaMART |
| MLflow | experiments/registry | MLflow + Postgres/artifacts volume |
| FastAPI | serving | Uvicorn/Gunicorn configuration after benchmark |
| Prometheus/Grafana | system/service observability | scrape + dashboards |
| Evidently | batch data/model monitoring | scheduled reports |
| Prefect | orchestration | scheduled retraining flows |

## Failure and degradation policy

| Сбой | Поведение API | Наблюдаемость |
|---|---|---|
| Redis недоступен | global/trending popularity fallback | dependency error counter, alert |
| ANN index недоступен | ALS + popularity candidates | retrieval-source availability |
| Ranker недоступен | weighted retrieval order | model fallback counter |
| Unknown user | segment popularity, затем global | cold-start metric |
| Invalid request | `422` без вызова models | request validation metric |

Ни один fallback не должен молча скрывать ошибку: он добавляет reason в логи/метрики, но не раскрывает внутренние детали клиенту.
