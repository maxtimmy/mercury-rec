# Данные и feature contracts

## Базовые сущности

| Entity | Primary key | Важные поля |
|---|---|---|
| `transaction` | `transaction_id` или deterministic event id | `user_id`, `item_id`, `event_type`, `event_time`, `price`, `channel_id` |
| `customer` | `user_id` | age segment, country/region (если доступно и разрешено), signup attributes |
| `article` | `item_id` | product type, category, colour, price, article metadata |

Raw data неизменяемы. Normalized tables добавляют `ingested_at`, `source_version`, `schema_version`, `event_id`.

## Event contract

Topic: `user-events.v1`. Ключ партиции: `user_id`.

```json
{
  "event_id": "uuid-or-deterministic-hash",
  "schema_version": 1,
  "user_id": "123",
  "item_id": "89214",
  "event_type": "purchase",
  "event_time": "2026-01-15T09:41:00Z",
  "price": 29.99,
  "currency": "EUR",
  "source": "hm-replay"
}
```

`event_id` обеспечивает idempotency. Некорректные события отправляются в `user-events.dlq` с причиной; consumer не должен останавливать partition.

## Point-in-time correctness

Для строки с label на `T` feature builder читает только записи с `event_time < T`. При этом:

- feature windows определяются относительно `T`, например `[T-30d, T)`;
- popularity строится из состояния до `T`;
- item embeddings/index и category mappings версионируются по cutoff;
- никакие future purchases, обновлённые labels или агрегаты целиком не попадают в training row.

## Начальный набор признаков

| Group | Feature | Window/definition |
|---|---|---|
| User | `purchases_7d`, `purchases_30d` | counts до request/label time |
| User | `avg_price_30d`, `days_since_last_purchase` | point-in-time aggregate |
| User | `top_category_30d` | deterministic tie-break |
| Item | `popularity_1d`, `popularity_7d` | unique users и purchases отдельно |
| Item | `item_age_days`, category/product metadata | versioned metadata |
| Cross | `category_affinity_30d` | user interaction share in item category |
| Cross | `price_distance` | abs(item price − user average price) |
| Cross | `embedding_similarity`, `previous_interactions` | snapshot-aware |

## Validation and privacy

- Проверять uniqueness IDs, null rates, timestamp range, price domain/currency and referential integrity.
- Не логировать raw personal attributes в API logs or dashboards.
- H&M data используется только в рамках его license/terms; provenance and checksum фиксируются до ingestion.
- Sensitive/proxy attributes не становятся ranking features без отдельного ADR и fairness assessment.
