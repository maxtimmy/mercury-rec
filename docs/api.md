# Recommendation API contract

## `GET /v1/recommendations/{user_id}`

### Query parameters

| Name | Type | Default | Constraints |
|---|---|---:|---|
| `limit` | integer | 20 | 1–100 |
| `request_context` | optional string | — | opaque, no PII |

### Successful response — `200`

```json
{
  "request_id": "01J...",
  "user_id": "user_123",
  "model_version": "ranking-v17",
  "generated_at": "2026-08-18T10:00:00Z",
  "recommendations": [
    {"item_id": "item_892", "score": 0.932, "rank": 1},
    {"item_id": "item_127", "score": 0.881, "rank": 2}
  ],
  "fallback": null
}
```

`score` — internal ordering score, не вероятность покупки и не предназначен для кросс-версий модели. При деградации `fallback` содержит стабильный код, например `"cold_start_segment_popularity"`.

### Errors

| Status | Code | Meaning |
|---:|---|---|
| 422 | `invalid_request` | Некорректный `user_id` or `limit` |
| 429 | `rate_limited` | Превышен лимит клиента |
| 503 | `recommendations_unavailable` | Все serving paths недоступны |

Ошибки имеют `{ "request_id", "code", "message" }`; в `message` нет инфраструктурных деталей.

## Operational endpoints

- `GET /health/live` — процесс жив, без зависимости от external services.
- `GET /health/ready` — обязательные зависимости и active model/index готовы.
- `GET /metrics` — Prometheus exposition; закрыт от public clients в реальном deploy.
