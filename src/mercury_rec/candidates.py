"""Leakage-safe candidate generators for the first stage of V2."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import polars as pl

from mercury_rec.retrieval import ALSModel, PopularityModel


@dataclass(frozen=True)
class CooccurrenceModel:
    """Item-to-item neighbours computed only from interactions before a cutoff."""

    neighbours: dict[str, list[str]]

    def recommend(self, history: pl.DataFrame, user_id: str, limit: int) -> list[str]:
        seen = history.filter(pl.col("user_id") == user_id).get_column("item_id").unique().to_list()
        scores: dict[str, int] = defaultdict(int)
        for item_id in seen:
            for neighbour in self.neighbours.get(item_id, []):
                if neighbour not in seen:
                    scores[neighbour] += 1
        return [
            item_id
            for item_id, _ in sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))[:limit]
        ]


def fit_item_cooccurrence(history: pl.DataFrame, max_neighbours: int = 100) -> CooccurrenceModel:
    """Fit bounded item co-occurrence from a caller-supplied cut-off history."""

    pairs: dict[tuple[str, str], int] = defaultdict(int)
    baskets = history.group_by("user_id").agg(pl.col("item_id").unique()).get_column("item_id")
    for items in baskets:
        ordered = sorted(items)
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

    rows: list[dict[str, object]] = []
    for user_id in sorted(set(users)):
        sources: list[tuple[str, list[str]]] = [
            ("popularity", popularity.recommend(user_id, per_source_limit))
        ]
        if als is not None:
            sources.append(("als", als.recommend(user_id, per_source_limit)))
        if cooccurrence is not None:
            sources.append(
                ("cooccurrence", cooccurrence.recommend(history, user_id, per_source_limit))
            )
        memberships: dict[str, dict[str, int]] = defaultdict(dict)
        for source, recommendations in sources:
            for rank, item_id in enumerate(recommendations, start=1):
                if available_items is None or item_id in available_items:
                    memberships[item_id].setdefault(source, rank)
        for item_id, ranks in memberships.items():
            rows.append(
                {
                    "user_id": user_id,
                    "item_id": item_id,
                    "sources": ",".join(sorted(ranks)),
                    "popularity_rank": ranks.get("popularity"),
                    "als_rank": ranks.get("als"),
                    "cooccurrence_rank": ranks.get("cooccurrence"),
                }
            )
    return pl.DataFrame(
        rows,
        schema={
            "user_id": pl.String,
            "item_id": pl.String,
            "sources": pl.String,
            "popularity_rank": pl.Int64,
            "als_rank": pl.Int64,
            "cooccurrence_rank": pl.Int64,
        },
    ).sort(["user_id", "item_id"])
