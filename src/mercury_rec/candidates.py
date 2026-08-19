"""Leakage-safe candidate generators for the first stage of V2."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

import polars as pl

from mercury_rec.retrieval import ALSModel, PopularityModel


@dataclass(frozen=True)
class CooccurrenceModel:
    """Item-to-item neighbours computed only from interactions before a cutoff."""

    neighbours: dict[str, list[str]]

    def recommend(self, seen: set[str], limit: int) -> list[str]:
        """Return deterministic neighbours, excluding items already purchased by the user."""

        scores: dict[str, int] = defaultdict(int)
        for item_id in seen:
            for neighbour in self.neighbours.get(item_id, []):
                if neighbour not in seen:
                    scores[neighbour] += 1
        return [
            item_id
            for item_id, _ in sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))[:limit]
        ]


def fit_item_cooccurrence(
    history: pl.DataFrame,
    cutoff: date,
    *,
    window_days: int,
    max_items_per_user: int,
    max_neighbours: int,
) -> CooccurrenceModel:
    """Fit a bounded, recent co-occurrence model from cut-off history only."""

    if window_days < 1 or max_items_per_user < 2 or max_neighbours < 1:
        raise ValueError("Co-occurrence limits must be positive and allow item pairs")

    pairs: dict[tuple[str, str], int] = defaultdict(int)
    window_start = cutoff - timedelta(days=window_days)
    baskets = (
        history.filter(pl.col("event_date") >= pl.lit(window_start))
        .sort(["user_id", "event_date", "item_id"], descending=[False, True, False])
        .group_by("user_id", maintain_order=True)
        .agg(pl.col("item_id").unique(maintain_order=True))
        .get_column("item_id")
    )
    for items in baskets:
        ordered = items[:max_items_per_user]
        for index, left in enumerate(ordered):
            for right in ordered[index + 1 :]:
                pairs[(left, right)] += 1
                pairs[(right, left)] += 1
    grouped: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for (item_id, neighbour), count in pairs.items():
        grouped[item_id].append((neighbour, count))
    return CooccurrenceModel(
        {
            item_id: [
                item for item, _ in sorted(values, key=lambda x: (-x[1], x[0]))[:max_neighbours]
            ]
            for item_id, values in grouped.items()
        }
    )


def build_candidate_pool(
    history: pl.DataFrame,
    users: list[str],
    popularity: PopularityModel,
    als: ALSModel | None,
    cooccurrence: CooccurrenceModel | None,
    *,
    per_source_limit: int,
    available_items: set[str] | None = None,
) -> pl.DataFrame:
    """Union candidates with attribution; unknown users get trending popularity only."""

    target_users = sorted(set(users))
    seen_by_user = {
        row["user_id"]: set(row["item_id"])
        for row in history.filter(pl.col("user_id").is_in(target_users))
        .group_by("user_id")
        .agg(pl.col("item_id").unique())
        .iter_rows(named=True)
    }
    source_columns: dict[str, tuple[list[str], list[str], list[int]]] = {}
    for user_id in target_users:
        sources: list[tuple[str, list[str]]] = [
            ("popularity", popularity.recommend(user_id, per_source_limit))
        ]
        if als is not None:
            sources.append(("als", als.recommend(user_id, per_source_limit)))
        if cooccurrence is not None:
            sources.append(
                (
                    "cooccurrence",
                    cooccurrence.recommend(seen_by_user.get(user_id, set()), per_source_limit),
                )
            )
        for source, recommendations in sources:
            items = [
                item
                for item in recommendations
                if available_items is None or item in available_items
            ]
            if items:
                user_ids, item_ids, ranks = source_columns.setdefault(source, ([], [], []))
                user_ids.extend([user_id] * len(items))
                item_ids.extend(items)
                ranks.extend(range(1, len(items) + 1))
    if not source_columns:
        return _empty_candidate_pool()
    source_frames = [
        pl.DataFrame(
            {
                "user_id": user_ids,
                "item_id": item_ids,
                "source": [source] * len(item_ids),
                "rank": ranks,
            }
        )
        for source, (user_ids, item_ids, ranks) in source_columns.items()
    ]
    grouped = (
        pl.concat(source_frames)
        .group_by(["user_id", "item_id"])
        .agg(
            pl.when(pl.col("source") == "popularity")
            .then(pl.col("rank"))
            .min()
            .alias("popularity_rank"),
            pl.when(pl.col("source") == "als").then(pl.col("rank")).min().alias("als_rank"),
            pl.when(pl.col("source") == "cooccurrence")
            .then(pl.col("rank"))
            .min()
            .alias("cooccurrence_rank"),
        )
    )
    return (
        grouped.with_columns(
            pl.concat_str(
                [
                    pl.when(pl.col("als_rank").is_not_null()).then(pl.lit("als")),
                    pl.when(pl.col("cooccurrence_rank").is_not_null()).then(pl.lit("cooccurrence")),
                    pl.when(pl.col("popularity_rank").is_not_null()).then(pl.lit("popularity")),
                ],
                separator=",",
                ignore_nulls=True,
            ).alias("sources")
        )
        .select("user_id", "item_id", "sources", "popularity_rank", "als_rank", "cooccurrence_rank")
        .sort(["user_id", "item_id"])
    )


def _empty_candidate_pool() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "user_id": pl.String,
            "item_id": pl.String,
            "sources": pl.String,
            "popularity_rank": pl.Int64,
            "als_rank": pl.Int64,
            "cooccurrence_rank": pl.Int64,
        }
    )
