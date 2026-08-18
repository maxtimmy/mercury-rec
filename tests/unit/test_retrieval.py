from datetime import date

import polars as pl

from mercury_rec.retrieval import fit_trending_popularity


def test_trending_popularity_uses_latest_window_and_stable_ties() -> None:
    history = pl.DataFrame(
        {
            "event_date": [date(2020, 1, 1), date(2020, 1, 7), date(2020, 1, 7), date(2020, 1, 7)],
            "item_id": ["old", "b", "a", "a"],
        }
    )

    model = fit_trending_popularity(history, window_days=1)

    assert model.recommend("any-user", 3) == ["a", "b"]
