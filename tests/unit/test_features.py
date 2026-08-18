from datetime import date

import polars as pl

from mercury_rec.features import build_point_in_time_features, label_candidate_rows


def test_features_exclude_future_interactions_at_cutoff() -> None:
    cutoff = date(2020, 1, 3)
    history = pl.DataFrame(
        {
            "event_date": [date(2020, 1, 1), date(2020, 1, 4)],
            "user_id": ["u1", "u1"],
            "item_id": ["a", "a"],
            "price": [10.0, 99.0],
        }
    )
    candidates = pl.DataFrame(
        {
            "user_id": ["u1"],
            "item_id": ["a"],
            "sources": ["popularity"],
            "popularity_rank": [1],
            "als_rank": [None],
            "cooccurrence_rank": [None],
        }
    )

    row = build_point_in_time_features(history, candidates, cutoff).row(0, named=True)

    assert row["user_purchase_count"] == 1
    assert row["user_average_price"] == 10.0
    assert row["user_item_days_since_last_purchase"] == 2


def test_labels_only_mark_items_that_are_already_candidates() -> None:
    rows = pl.DataFrame({"user_id": ["u1", "u1"], "item_id": ["a", "b"]})
    assert label_candidate_rows(rows, {"u1": {"a", "future-not-in-pool"}}).get_column(
        "label"
    ).to_list() == [1, 0]
