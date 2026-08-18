# ADR-001 — Two-stage retrieval and ranking

Status: accepted
Date: 2026-08-18

## Context

Ранжировать весь catalog на запросе дорого, а simple popularity не персонализирует выдачу. Нужны отдельные измеримые retrieval и ranking layers.

## Decision

Использовать multi-source candidate generation с фиксируемым budget, затем LightGBM ranker для candidate pairs. Popularity остаётся первым baseline и fallback.

## Alternatives considered

- Single-stage ranker over full catalog — не соответствует latency budget.
- Только ALS — слабее для content/cold-start signals.
- Только neural end-to-end ranker — сложнее baseline, debugging и local serving.

## Consequences

Нужно versioning candidate snapshots, source attribution и отдельные Recall@K. Улучшение ranker не компенсирует target, потерянный retrieval.

## Validation / rollback

Сравнить candidate recall, NDCG, coverage и serving latency на одинаковом temporal split. При failure ranker отдавать deterministic candidate ordering.
