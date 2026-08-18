# ADR-005 — Offline/online feature consistency

Status: accepted
Date: 2026-08-18

## Context

Разные SQL/Python/API реализации feature logic создают training-serving skew и leakage risk.

## Decision

Feature definitions versioned in Feast/reusable transformations; offline joins use point-in-time retrieval and online fields have the same documented semantics, units and ownership.

## Alternatives considered

- Duplicated feature code — быстрее вначале, но высокий skew risk.
- Только offline features — не выполняет online serving goal.

## Consequences

Нужны contract/parity tests, schema versions and explicit materialization ownership.

## Validation / rollback

Compare offline and online values on fixed entity-time fixtures; block promotion/materialization on mismatch or unknown unit/schema.
