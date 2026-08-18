# ML-подход и offline evaluation

## Two-stage pipeline

### Candidate generation

Каждый источник возвращает ranked list и source score:

1. global/segment/trending popularity — обязательный baseline и fallback;
2. item-item similarity — co-occurrence / embeddings;
3. implicit ALS или BPR — collaborative filtering baseline;
4. two-tower — user/item embeddings и ANN search.

Списки объединяются, deduplicate-ятся по `item_id`, получают provenance и обрезаются кандидато-бюджетом. Candidate recall измеряется до ranker.

### Ranking

LightGBM LambdaMART ранжирует candidate pairs, используя признаки из [data-and-features.md](data-and-features.md). Labels сначала: next purchase within horizon. Negative samples берутся только из доступного на момент `T` catalog/candidate pool; policy (ratio, sources, seed) сохраняется в MLflow.

Post-ranking rules не обучаются неявно: availability, already-bought policy, category/item caps и diversity явно конфигурируются и измеряются.

## Temporal evaluation protocol

- Train/validation/test идут строго во времени; exact boundaries — в versioned config.
- Для каждого test interaction target item считается релевантным, кандидаты и features строятся до interaction time.
- Все models, indices, feature snapshots fit/materialized только на разрешённом прошлом.
- Validation служит selection/hyperparameter tuning; test открывается для финального отчёта, не для итеративного tuning.

## Метрики

| Layer | Metrics | Зачем |
|---|---|---|
| Retrieval | Recall@50/100/200, source contribution | Может ли ranker вообще увидеть target |
| Ranking | NDCG@10, MRR@10, Recall@10 | Позиционное качество top-N |
| Catalog | coverage, concentration, novelty, diversity | Контроль popularity bias и узкого выдачи |
| Serving | P50/P95/P99, RPS, error rate | Инженерная пригодность |
| Monitoring | feature missingness, drift, score distribution | Раннее обнаружение skew/regression |

Срезы обязательны минимум по warm/cold users, activity buckets и item popularity buckets. Нельзя объявлять CTR — в историческом implicit dataset без proper counterfactual/online experiment это proxy, а не causal impact.

## Promotion quality gate

Challenger можно продвигать, только если:

- улучшает заранее зафиксированную primary metric на validation больше practical threshold;
- не нарушает guardrails coverage/diversity/latency;
- data validation и training reproducibility прошли;
- comparison сделан с тем же dataset split, feature snapshot и candidate policy.

Threshold и допустимые регрессии должны быть конфигурацией, а не скрытым кодом.
