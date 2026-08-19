from datetime import date

import polars as pl
from pytest import approx

from mercury_rec.quality import transaction_quality_report


def test_transaction_quality_report_contains_only_aggregate_statistics() -> None:
    transactions = pl.DataFrame(
        {
            "event_date": [date(2020, 1, 1), date(2020, 1, 1), date(2020, 1, 2)],
            "user_id": ["u1", "u1", "u2"],
            "item_id": ["a", "a", "b"],
            "price": [10.0, 10.0, 20.0],
            "sales_channel_id": [1, 1, 2],
        }
    )

    report = transaction_quality_report(transactions)

    assert report["rows"] == 3
    assert report["duplicate_rate"] == approx(1 / 3)
    assert report["null_rates"]["price"] == 0.0
    assert report["users"]["entities"] == 2
    assert report["price"]["p50"] == 10.0
