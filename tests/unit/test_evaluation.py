from pytest import approx

from mercury_rec.evaluation import evaluate_rankings


def test_rank_metrics_reward_relevant_early_items() -> None:
    metrics = evaluate_rankings(
        recommendations={"u1": ["a", "x"], "u2": ["x", "b"]},
        labels={"u1": {"a"}, "u2": {"b", "c"}},
        catalog_items={"a", "b", "c", "x"},
        item_counts={"a": 2, "b": 1, "x": 4},
        k_values=[2],
    )

    assert metrics["recall_at_2"] == approx(0.75)
    assert metrics["mrr_at_2"] == approx(0.75)
    assert metrics["coverage_at_2"] == approx(0.75)
    assert metrics["diversity_at_2"] == approx(1.0)
