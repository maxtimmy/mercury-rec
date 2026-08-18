# Architecture Decision Records

ADR фиксирует контекст, принятое решение, альтернативы и последствия. Он краткий, неизменяем после acceptance; новая информация создаёт superseding ADR. Шаблон ниже.

```markdown
# ADR-NNN — Title
Status: proposed | accepted | superseded
Date: YYYY-MM-DD

## Context
## Decision
## Alternatives considered
## Consequences
## Validation / rollback
```

## Index

- [ADR-001: Two-stage retrieval and ranking](ADR-001-two-stage-recommendation.md)
- [ADR-002: Redis for online feature access](ADR-002-redis-online-features.md)
- [ADR-003: LightGBM LambdaMART ranker](ADR-003-lightgbm-ranker.md)
- [ADR-004: Batch plus stream features](ADR-004-batch-stream-features.md)
- [ADR-005: Offline/online feature consistency](ADR-005-feature-consistency.md)
