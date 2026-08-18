# План реализации

## Definition of Done для любой версии

- Код форматирован, type-checked и покрыт уместными тестами.
- Команда запуска и требуемые сервисы описаны в README версии/PR.
- Конфигурация и dataset/model version сохранены вместе с результатом.
- Метрики получены на зафиксированном temporal split и воспроизводимы.
- Добавлены или обновлены релевантные docs/ADR.

## V0 — Foundation

**Цель:** создать воспроизводимый каркас, не ML-систему.

- [ ] Инициализировать Python-проект, линтер, тесты и pre-commit.
- [ ] Добавить `docker-compose.yml` для Postgres, Redis, MLflow, Prometheus, Grafana; Redpanda — profile/следующая версия.
- [ ] Добавить config schema (Hydra/Pydantic) и `.env.example` без секретов.
- [ ] Настроить CI: lint, unit tests, build image.
- [ ] Определить dataset version/checksum и data license в [dataset.md](dataset.md).

**Acceptance:** чистый checkout проходит проверку и поднимает пустую локальную инфраструктуру одной documented-командой.

## V1 — Offline baseline

- [ ] Ingest H&M customers, articles, transactions с schema validation.
- [ ] Реализовать temporal split: train Jan–May, validation 1–15 Jun, test 16–30 Jun (точные даты зависят от доступного периода и фиксируются в config).
- [ ] Реализовать popularity baseline: global, country/age segment, trending window.
- [ ] Реализовать implicit ALS/BPR baseline.
- [ ] Посчитать Recall@K, NDCG@K, MRR@K, coverage и novelty; сохранить результаты.

**Gate:** нет событий из validation/test в train, features или candidate indices прошлого времени.

## V2 — Two-stage recommender

- [ ] Объединить источники кандидатов: popularity, item-item, ALS/BPR; дедупликация и source attribution.
- [ ] Добавить two-tower retrieval и ANN index (FAISS локально; Qdrant — опционально после замера нужды).
- [ ] Сформировать point-in-time user/item/cross features.
- [ ] Обучить LightGBM ranker с групповыми queries и explicit negative sampling policy.
- [ ] Добавить cold-start fallbacks и business rules (availability, dedupe, diversity cap).

**Gate:** есть ablation таблица: каждый retrieval source, candidate recall и ranker uplift относительно baseline.

## V3 — Online serving

- [ ] FastAPI endpoint по [api.md](api.md), readiness/liveness и structured logs.
- [ ] Online feature lookup в Redis; model/index version в ответе.
- [ ] Docker image и integration test с локальными dependencies.
- [ ] Locust/k6 сценарии: warm user, cold user, invalid user, degraded dependency.

**Gate:** опубликованы реальные P50/P95/P99, RPS, error rate, machine/configuration и duration теста.

## V4 — MLOps

- [ ] Feature definitions в Feast, offline и online materialization.
- [ ] MLflow tracking: data version, git SHA, config, features, metrics, artifacts.
- [ ] Champion/challenger registry policy.
- [ ] Prefect (предпочтительно) flow: validate → features → train → evaluate → register → promote.

**Gate:** quality gate не продвигает модель при отсутствии статистически/практически значимого улучшения или нарушении guardrails.

## V5 — Streaming

- [ ] Event contract и Redpanda topic.
- [ ] Replay транзакций с контролируемой скоростью и idempotency key.
- [ ] Consumer обновляет последние взаимодействия, popularity и category affinity.
- [ ] Измерить event-to-feature freshness.

**Gate:** повтор события не меняет агрегат дважды; lag и DLQ наблюдаемы.

## V6/V7 — Production behaviour and polish

- [ ] Prometheus metrics, Grafana dashboards, alerts, Evidently batch drift report.
- [ ] Simulated price-unit incident, rollback/recovery и заполненный postmortem.
- [ ] ADR для существенных решений, system-design document, cost/latency trade-off.
- [ ] CI integration/load smoke tests, dependency/security checks.

**Gate:** incident обнаруживается мониторингом; документация позволяет другому инженеру воспроизвести demo и объяснить компромиссы.
