# ADR-004 — Batch plus stream features

Status: accepted
Date: 2026-08-18

## Context

Долгие aggregates проще и дешевле считать batch, а recent interactions/trending signal требуют свежести.

## Decision

Batch pipeline строит historical PIT features; Redpanda consumer обновляет ограниченный набор online aggregates: last interactions, recent category affinity and item popularity.

## Alternatives considered

- Batch-only — проще, но не демонстрирует freshness/replay path.
- Streaming-first for all features — неоправданная сложность.

## Consequences

Нужны clear feature ownership, idempotency, freshness SLI and reconciliation job.

## Validation / rollback

Replay fixed events, compare expected aggregates, verify duplicate handling and report event-to-feature latency.
