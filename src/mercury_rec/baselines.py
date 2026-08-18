"""Orchestration for V1 offline baseline training and evaluation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import polars as pl
import yaml

from mercury_rec.data import (
    EvaluationPeriod,
    history_before,
    labels_between,
    load_transactions,
    make_temporal_split,
)
from mercury_rec.evaluation import evaluate_rankings
from mercury_rec.retrieval import fit_als, fit_trending_popularity


@dataclass(frozen=True)
class BaselineConfig:
    raw_dir: Path
    processed_dir: Path
    artifacts_dir: Path
    horizon_days: int
    popularity_window_days: int
    recommendation_limit: int
    als_factors: int
    als_regularization: float
    als_iterations: int
    als_random_seed: int
    k_values: list[int]


def load_baseline_config(path: Path) -> BaselineConfig:
    """Load the minimal V1 configuration from versioned YAML."""

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return BaselineConfig(
        raw_dir=Path(payload["dataset"]["raw_dir"]),
        processed_dir=Path(payload["dataset"]["processed_dir"]),
        artifacts_dir=Path(payload["dataset"]["artifacts_dir"]),
        horizon_days=payload["split"]["horizon_days"],
        popularity_window_days=payload["popularity"]["window_days"],
        recommendation_limit=payload["popularity"]["recommendation_limit"],
        als_factors=payload["als"]["factors"],
        als_regularization=payload["als"]["regularization"],
        als_iterations=payload["als"]["iterations"],
        als_random_seed=payload["als"]["random_seed"],
        k_values=payload["evaluation"]["k_values"],
    )


def run_baselines(config: BaselineConfig) -> Path:
    """Train and evaluate popularity/ALS on validation and test temporal windows."""

    transactions = load_transactions(config.processed_dir)
    articles = pl.read_parquet(config.processed_dir / "articles.parquet")
    catalog_items = set(articles["item_id"].to_list())
    split = make_temporal_split(transactions, config.horizon_days)
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "config": _jsonable_config(config),
        "split": asdict(split),
        "periods": {
            period.name: _evaluate_period(transactions, catalog_items, period, config)
            for period in (split.validation, split.test)
        },
    }
    config.artifacts_dir.mkdir(parents=True, exist_ok=True)
    path = config.artifacts_dir / f"baseline-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(
        json.dumps(report, indent=2, default=str, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def _evaluate_period(
    transactions: pl.DataFrame,
    catalog_items: set[str],
    period: EvaluationPeriod,
    config: BaselineConfig,
) -> dict[str, object]:
    history = history_before(transactions, period.cutoff)
    labels = labels_between(transactions, period)
    popularity = fit_trending_popularity(history, config.popularity_window_days)
    recommendations = {
        user_id: popularity.recommend(user_id, config.recommendation_limit) for user_id in labels
    }
    result: dict[str, object] = {
        "cutoff": period.cutoff.isoformat(),
        "label_end": period.label_end.isoformat(),
        "target_users": len(labels),
        "popularity": evaluate_rankings(
            recommendations, labels, catalog_items, popularity.item_counts, config.k_values
        ),
    }
    als = fit_als(
        history,
        factors=config.als_factors,
        regularization=config.als_regularization,
        iterations=config.als_iterations,
        random_seed=config.als_random_seed,
        fallback=popularity,
    )
    als_recommendations = {
        user_id: als.recommend(user_id, config.recommendation_limit) for user_id in labels
    }
    result["als"] = evaluate_rankings(
        als_recommendations, labels, catalog_items, popularity.item_counts, config.k_values
    )
    return result


def _jsonable_config(config: BaselineConfig) -> dict[str, object]:
    result = asdict(config)
    return {key: str(value) if isinstance(value, Path) else value for key, value in result.items()}
