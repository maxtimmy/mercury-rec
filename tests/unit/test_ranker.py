from datetime import date

import polars as pl

from mercury_rec.features import build_point_in_time_features, label_candidate_rows
from mercury_rec.ranker import fit_lambdamart


def test_synthetic_candidates_features_and_ranker_produce_ranked_response() -> None:
    cutoff = date(2020, 1, 4)
    history = pl.DataFrame(
        {
            "event_date": [date(2020, 1, 1), date(2020, 1, 2), date(2020, 1, 2), date(2020, 1, 3)],
            "user_id": ["u1", "u1", "u2", "u2"],
            "item_id": ["a", "a", "b", "b"],
            "price": [1.0, 1.0, 2.0, 2.0],
        }
    )
    candidates = pl.DataFrame(
        {
            "user_id": ["u1", "u1", "u2", "u2"],
            "item_id": ["a", "x", "b", "x"],
            "sources": ["als", "popularity", "als", "popularity"],
            "popularity_rank": [None, 1, None, 1],
            "als_rank": [1, None, 1, None],
            "cooccurrence_rank": [None, None, None, None],
        }
    )
    rows = label_candidate_rows(
        build_point_in_time_features(history, candidates, cutoff), {"u1": {"a"}, "u2": {"b"}}
    )

    ranked = fit_lambdamart(rows, n_estimators=5).rank(rows, limit=2)

    assert set(ranked) == {"u1", "u2"}
    assert all(len(items) == 2 for items in ranked.values())
