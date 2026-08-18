"""Leakage-free offline metrics for ranked recommendation lists."""

from __future__ import annotations

from math import log2


def evaluate_rankings(
    recommendations: dict[str, list[str]],
    labels: dict[str, set[str]],
    catalog_items: set[str],
    item_counts: dict[str, int],
    k_values: list[int],
) -> dict[str, float]:
    """Compute user-averaged ranking and catalog metrics at requested cutoffs."""

    if not labels:
        raise ValueError("Cannot evaluate without target users")
    total_events = sum(item_counts.values())
    results: dict[str, float] = {}
    for k in k_values:
        ranked = [recommendations.get(user_id, [])[:k] for user_id in labels]
        results[f"recall_at_{k}"] = sum(
            len(set(items) & labels[user_id]) / len(labels[user_id])
            for items, user_id in zip(ranked, labels, strict=True)
        ) / len(labels)
        results[f"ndcg_at_{k}"] = sum(
            _ndcg(items, labels[user_id]) for items, user_id in zip(ranked, labels, strict=True)
        ) / len(labels)
        results[f"mrr_at_{k}"] = sum(
            _mrr(items, labels[user_id]) for items, user_id in zip(ranked, labels, strict=True)
        ) / len(labels)
        recommended_items = {item for items in ranked for item in items}
        results[f"coverage_at_{k}"] = (
            len(recommended_items) / len(catalog_items) if catalog_items else 0.0
        )
        results[f"novelty_at_{k}"] = _novelty(ranked, item_counts, total_events)
    return results


def _ndcg(items: list[str], labels: set[str]) -> float:
    dcg = sum(1 / log2(index + 2) for index, item in enumerate(items) if item in labels)
    ideal = sum(1 / log2(index + 2) for index in range(min(len(items), len(labels))))
    return dcg / ideal if ideal else 0.0


def _mrr(items: list[str], labels: set[str]) -> float:
    for index, item in enumerate(items):
        if item in labels:
            return 1 / (index + 1)
    return 0.0


def _novelty(ranked: list[list[str]], item_counts: dict[str, int], total_events: int) -> float:
    items = [item for recommendations in ranked for item in recommendations]
    if not items or not total_events:
        return 0.0
    return sum(-log2(item_counts.get(item, 1) / total_events) for item in items) / len(items)
