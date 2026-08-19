"""Aggregate, non-sensitive data quality summaries for offline experiments."""

from __future__ import annotations

from datetime import date
from typing import Any, cast

import polars as pl


def transaction_quality_report(transactions: pl.DataFrame) -> dict[str, Any]:
    """Return reproducible data-quality aggregates for normalized transactions."""

    if transactions.is_empty():
        raise ValueError("Cannot create a quality report for empty transactions")
    rows = transactions.height
    duplicate_rows = rows - transactions.unique().height
    null_rates = {
        column: transactions.get_column(column).null_count() / rows
        for column in transactions.columns
    }
    user_activity = transactions.group_by("user_id").len().get_column("len")
    item_activity = transactions.group_by("item_id").len().get_column("len")
    event_dates = transactions.get_column("event_date")
    min_date = event_dates.min()
    max_date = event_dates.max()
    if not isinstance(min_date, date) or not isinstance(max_date, date):
        raise ValueError("event_date must be a date column")
    return {
        "rows": rows,
        "duplicate_rate": duplicate_rows / rows,
        "null_rates": null_rates,
        "date_range": {"min": min_date.isoformat(), "max": max_date.isoformat()},
        "users": _activity_summary(user_activity),
        "items": _activity_summary(item_activity),
        "price": {
            "min": _float(transactions.get_column("price").min()),
            "p50": _float(transactions.get_column("price").median()),
            "p95": _float(transactions.get_column("price").quantile(0.95)),
            "max": _float(transactions.get_column("price").max()),
        },
    }


def _activity_summary(activity: pl.Series) -> dict[str, float | int]:
    return {
        "entities": activity.len(),
        "mean": _float(activity.mean()),
        "p50": _float(activity.median()),
        "p95": _float(activity.quantile(0.95)),
        "max": int(cast(Any, activity.max())),
    }


def _float(value: object) -> float:
    return float(cast(Any, value))
