"""LightGBM LambdaMART second-stage ranker."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl

from mercury_rec.features import FEATURE_COLUMNS


@dataclass
class LambdaMARTRanker:
    """A small wrapper around the LightGBM model used by V2."""

    model: Any

    def rank(self, rows: pl.DataFrame, limit: int) -> dict[str, list[str]]:
        scored = rows.with_columns(
            pl.Series("score", self.model.predict(rows.select(FEATURE_COLUMNS).to_numpy()))
        ).sort(["user_id", "score", "item_id"], descending=[False, True, False])
        return {
            str(user_id[0]): group.get_column("item_id").head(limit).to_list()
            for user_id, group in scored.group_by("user_id", maintain_order=True)
        }


def fit_lambdamart(
    rows: pl.DataFrame, *, random_seed: int = 42, n_estimators: int = 100
) -> LambdaMARTRanker:
    """Fit LambdaMART grouped by user on labeled point-in-time candidates."""

    try:
        from lightgbm import LGBMRanker
    except ImportError as error:  # pragma: no cover
        raise RuntimeError(
            "Install mercury-rec with the lightgbm dependency to train V2."
        ) from error
    training = rows.sort("user_id")
    groups = training.group_by("user_id", maintain_order=True).len().get_column("len").to_list()
    model = LGBMRanker(
        objective="lambdarank",
        metric="ndcg",
        eval_at=[10],
        n_estimators=n_estimators,
        random_state=random_seed,
        n_jobs=1,
    )
    model.fit(
        training.select(FEATURE_COLUMNS).to_numpy(), training["label"].to_numpy(), group=groups
    )
    return LambdaMARTRanker(model)
