# ADR-002 — Redis for online feature access

Status: accepted
Date: 2026-08-18

## Context

API нужен быстрый lookup свежих user/item aggregates; offline warehouse не подходит для request path.

## Decision

Использовать Redis как online store, materialized через Feast/features pipeline. Store содержит только serving-ready aggregates with TTL/version metadata.

## Alternatives considered

- Direct Postgres reads — проще, но вероятно хуже tail latency/scaling.
- Полностью in-process cache — сложнее freshness и invalidation.

## Consequences

Потребуются cache consistency, monitoring missingness and degradation fallback. Redis не является source of truth.

## Validation / rollback

Benchmark lookup latency and PIT parity checks. При outage serve fallback popularity and alert.
