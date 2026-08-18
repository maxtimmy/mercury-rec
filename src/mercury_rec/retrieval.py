"""Offline candidate-generation baselines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import polars as pl
from implicit.cpu.als import AlternatingLeastSquares
from scipy.sparse import csr_matrix


@dataclass(frozen=True)
class PopularityModel:
    """Globally ranked trending items with deterministic ties."""

    ranked_items: list[str]
    item_counts: dict[str, int]

    def recommend(self, _: str, limit: int) -> list[str]:
        return self.ranked_items[:limit]


def fit_trending_popularity(history: pl.DataFrame, window_days: int) -> PopularityModel:
    """Fit popularity from the latest window available before a cutoff."""

    max_date = history.get_column("event_date").max()
    if not isinstance(max_date, date):
        return PopularityModel([], {})
    window_start = max_date - timedelta(days=window_days - 1)
    recent = history.filter(pl.col("event_date") >= pl.lit(window_start))
    counts = recent.group_by("item_id").len().sort(
        ["len", "item_id"], descending=[True, False]
    )
    if counts.is_empty():
        counts = history.group_by("item_id").len().sort(
            ["len", "item_id"], descending=[True, False]
        )
    item_ids = counts.get_column("item_id").to_list()
    item_counts = counts.get_column("len").to_list()
    return PopularityModel(
        ranked_items=item_ids,
        item_counts=dict(zip(item_ids, item_counts, strict=True)),
    )


class ALSModel:
    """Implicit-feedback ALS with popularity fallback for unknown users."""

    def __init__(
        self,
        model: AlternatingLeastSquares,
        user_ids: list[str],
        item_ids: list[str],
        user_items: csr_matrix,
        fallback: PopularityModel,
    ) -> None:
        self._model = model
        self._user_index = {user_id: index for index, user_id in enumerate(user_ids)}
        self._item_ids = item_ids
        self._user_items = user_items
        self._fallback = fallback

    def recommend(self, user_id: str, limit: int) -> list[str]:
        user_index = self._user_index.get(user_id)
        if user_index is None:
            return self._fallback.recommend(user_id, limit)
        item_indices, _ = self._model.recommend(
            user_index,
            self._user_items[user_index],
            N=limit,
            filter_already_liked_items=False,
        )
        return [self._item_ids[int(index)] for index in item_indices]


def fit_als(
    history: pl.DataFrame,
    *,
    factors: int,
    regularization: float,
    iterations: int,
    random_seed: int,
    fallback: PopularityModel,
) -> ALSModel:
    """Fit ALS from aggregated purchase counts before a temporal cutoff."""

    interactions = history.group_by(["user_id", "item_id"]).len()
    user_ids = sorted(interactions.get_column("user_id").unique().to_list())
    item_ids = sorted(interactions.get_column("item_id").unique().to_list())
    user_index = {user_id: index for index, user_id in enumerate(user_ids)}
    item_index = {item_id: index for index, item_id in enumerate(item_ids)}
    rows = np.fromiter((user_index[value] for value in interactions["user_id"]), dtype=np.int32)
    columns = np.fromiter((item_index[value] for value in interactions["item_id"]), dtype=np.int32)
    values = interactions["len"].to_numpy().astype(np.float32)
    user_items = csr_matrix((values, (rows, columns)), shape=(len(user_ids), len(item_ids)))
    model = AlternatingLeastSquares(
        factors=factors,
        regularization=regularization,
        iterations=iterations,
        random_state=random_seed,
        num_threads=1,
    )
    model.fit(user_items)
    return ALSModel(model, user_ids, item_ids, user_items, fallback)
