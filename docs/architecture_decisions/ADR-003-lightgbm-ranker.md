# ADR-003 — LightGBM LambdaMART ranker

Status: accepted
Date: 2026-08-18

## Context

На табличных user/item/cross features нужен сильный, объяснимый и быстро обучаемый ranking baseline.

## Decision

Начать с LightGBM LambdaMART; classifier допустим только как промежуточный baseline и явно не называется LTR.

## Alternatives considered

- Transformer ranker — более дорогой и сложный для first production-like iteration.
- Logistic regression — valuable baseline, но ограниченная feature interaction capacity.

## Consequences

Нужны group/query construction, objective-aware labels and sampling, feature importance sanity checks. Pair score не probability.

## Validation / rollback

Compare NDCG/MRR, calibration only where relevant, latency and feature ablations; rollback to validated prior registry version.
