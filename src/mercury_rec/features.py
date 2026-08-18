"""Point-in-time feature construction for V2 ranking rows."""

from __future__ import annotations

from datetime import date

import polars as pl

FEATURE_COLUMNS = [
    "user_purchase_count",
    "user_days_since_last_purchase",
    "user_average_price",
    "item_purchase_count",
    "item_average_price",
    "item_category_purchase_count",
    "user_item_purchase_count",
    "user_item_days_since_last_purchase",
    "from_popularity",
    "from_als",
    "from_cooccurrence",
]


def build_point_in_time_features(
    history: pl.DataFrame,
    candidates: pl.DataFrame,
    cutoff: date,
    articles: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Join candidates to features observable strictly before ``cutoff``."""

    safe = history.filter(pl.col("event_date") < pl.lit(cutoff))
    user = safe.group_by("user_id").agg(
        pl.len().alias("user_purchase_count"),
        (pl.lit(cutoff) - pl.col("event_date").max())
        .dt.total_days()
        .alias("user_days_since_last_purchase"),
        pl.col("price").mean().alias("user_average_price"),
    )
    item = safe.group_by("item_id").agg(
        pl.len().alias("item_purchase_count"), pl.col("price").mean().alias("item_average_price")
    )
    affinity = safe.group_by(["user_id", "item_id"]).agg(
        pl.len().alias("user_item_purchase_count"),
        (pl.lit(cutoff) - pl.col("event_date").max())
        .dt.total_days()
        .alias("user_item_days_since_last_purchase"),
    )
    result = (
        candidates.join(user, on="user_id", how="left")
        .join(item, on="item_id", how="left")
        .join(affinity, on=["user_id", "item_id"], how="left")
    )
    if articles is not None and "product_type_name" in articles.columns:
        categories = articles.select(
            "item_id", pl.col("product_type_name").cast(pl.String).alias("category")
        )
        counts = (
            safe.join(categories, on="item_id", how="left")
            .group_by("category")
            .len()
            .rename({"len": "item_category_purchase_count"})
        )
        result = result.join(categories, on="item_id", how="left").join(
            counts, on="category", how="left"
        )
    else:
        result = result.with_columns(pl.lit(0).alias("item_category_purchase_count"))
    return result.with_columns(
        pl.col("user_purchase_count").fill_null(0),
        pl.col("user_days_since_last_purchase").fill_null(-1),
        pl.col("user_average_price").fill_null(0.0),
        pl.col("item_purchase_count").fill_null(0),
        pl.col("item_average_price").fill_null(0.0),
        pl.col("item_category_purchase_count").fill_null(0),
        pl.col("user_item_purchase_count").fill_null(0),
        pl.col("user_item_days_since_last_purchase").fill_null(-1),
        pl.col("sources").str.contains("popularity").cast(pl.Int8).alias("from_popularity"),
        pl.col("sources").str.contains("als").cast(pl.Int8).alias("from_als"),
        pl.col("sources").str.contains("cooccurrence").cast(pl.Int8).alias("from_cooccurrence"),
    )


def label_candidate_rows(rows: pl.DataFrame, labels: dict[str, set[str]]) -> pl.DataFrame:
    """Attach labels to existing candidates only, yielding valid in-pool negatives."""

    return rows.with_columns(
        pl.struct("user_id", "item_id")
        .map_elements(
            lambda value: int(value["item_id"] in labels.get(value["user_id"], set())),
            return_dtype=pl.Int8,
        )
        .alias("label")
    )
