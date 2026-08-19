from datetime import date

import polars as pl

from mercury_rec.candidates import build_candidate_pool, fit_item_cooccurrence
from mercury_rec.retrieval import fit_trending_popularity


def _history() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "event_date": [date(2020, 1, 1), date(2020, 1, 1), date(2020, 1, 2), date(2020, 1, 2)],
            "user_id": ["u1", "u1", "u2", "u2"],
            "item_id": ["a", "b", "a", "c"],
            "price": [1.0, 2.0, 1.0, 3.0],
        }
    )


def test_candidate_pool_deduplicates_and_keeps_source_attribution() -> None:
    history = _history()
    pool = build_candidate_pool(
        history,
        ["u1"],
        fit_trending_popularity(history, 7),
        None,
        fit_item_cooccurrence(
            history, date(2020, 1, 3), window_days=90, max_items_per_user=20, max_neighbours=100
        ),
        per_source_limit=3,
        available_items={"a", "b", "c"},
    )

    assert pool.filter(pl.col("item_id") == "c").item(0, "sources") == "cooccurrence,popularity"
    assert pool.group_by(["user_id", "item_id"]).len().get_column("len").max() == 1


def test_candidate_pool_filters_unknown_items_and_cold_user_uses_popularity() -> None:
    history = _history()
    pool = build_candidate_pool(
        history,
        ["new"],
        fit_trending_popularity(history, 7),
        None,
        fit_item_cooccurrence(
            history, date(2020, 1, 3), window_days=90, max_items_per_user=20, max_neighbours=100
        ),
        per_source_limit=3,
        available_items={"a"},
    )

    assert pool.get_column("item_id").to_list() == ["a"]
    assert pool.item(0, "sources") == "popularity"


def test_cooccurrence_uses_only_recent_window_and_bounded_user_history() -> None:
    history = pl.DataFrame(
        {
            "event_date": [date(2020, 1, 1), date(2020, 1, 9), date(2020, 1, 9), date(2020, 1, 10)],
            "user_id": ["old", "recent", "recent", "recent"],
            "item_id": ["old-a", "a", "b", "c"],
            "price": [1.0, 1.0, 1.0, 1.0],
        }
    )

    model = fit_item_cooccurrence(
        history, date(2020, 1, 11), window_days=3, max_items_per_user=2, max_neighbours=10
    )

    assert "old-a" not in model.neighbours
    assert model.recommend({"a"}, 10) == ["c"]
