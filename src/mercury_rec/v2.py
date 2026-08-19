"""Offline V2 two-stage benchmark orchestration."""

from __future__ import annotations

import json
import resource
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import polars as pl
import yaml

from mercury_rec.candidates import build_candidate_pool, fit_item_cooccurrence
from mercury_rec.data import (
    EvaluationPeriod,
    history_before,
    labels_between,
    load_transactions,
    make_temporal_split,
)
from mercury_rec.evaluation import evaluate_rankings
from mercury_rec.features import build_point_in_time_features, label_candidate_rows
from mercury_rec.quality import transaction_quality_report
from mercury_rec.ranker import fit_lambdamart
from mercury_rec.retrieval import fit_als, fit_trending_popularity


@dataclass(frozen=True)
class V2Config:
    processed_dir: Path
    artifacts_dir: Path
    horizon_days: int
    popularity_window_days: int
    per_source_limit: int
    cooccurrence_window_days: int
    cooccurrence_max_items_per_user: int
    cooccurrence_max_neighbours: int
    ranking_limit: int
    als_factors: int
    als_regularization: float
    als_iterations: int
    random_seed: int
    k_values: list[int]


def load_v2_config(path: Path) -> V2Config:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return V2Config(
        Path(payload["dataset"]["processed_dir"]),
        Path(payload["dataset"]["artifacts_dir"]),
        payload["split"]["horizon_days"],
        payload["popularity"]["window_days"],
        payload["candidates"]["per_source_limit"],
        payload["cooccurrence"]["window_days"],
        payload["cooccurrence"]["max_items_per_user"],
        payload["cooccurrence"]["max_neighbours"],
        payload["ranker"]["ranking_limit"],
        payload["als"]["factors"],
        payload["als"]["regularization"],
        payload["als"]["iterations"],
        payload["als"]["random_seed"],
        payload["evaluation"]["k_values"],
    )


def run_v2_benchmark(config: V2Config) -> Path:
    """Fit on validation labels, evaluate candidate ablations and ranker on test."""
    transactions = load_transactions(config.processed_dir)
    articles = pl.read_parquet(config.processed_dir / "articles.parquet")
    catalog = set(articles.get_column("item_id").to_list())
    split = make_temporal_split(transactions, config.horizon_days)
    validation_started = perf_counter()
    validation_rows, _ = _feature_rows_for_period(
        transactions, articles, catalog, split.validation, config
    )
    validation_feature_seconds = perf_counter() - validation_started
    train_rows = label_candidate_rows(
        validation_rows,
        labels_between(transactions, split.validation),
    )
    train_started = perf_counter()
    ranker = fit_lambdamart(train_rows, random_seed=config.random_seed)
    train_seconds = perf_counter() - train_started
    test_started = perf_counter()
    test_rows, pool = _feature_rows_for_period(transactions, articles, catalog, split.test, config)
    test_feature_seconds = perf_counter() - test_started
    source_rankings = _source_rankings(pool)
    target = labels_between(transactions, split.test)
    counts = fit_trending_popularity(
        history_before(transactions, split.test.cutoff), config.popularity_window_days
    ).item_counts
    inference_started = perf_counter()
    ranked = ranker.rank(test_rows, config.ranking_limit)
    inference_seconds = perf_counter() - inference_started
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "config": _jsonable_config(config),
        "split": asdict(split),
        "primary_metric": "ndcg_at_10",
        "guardrails": ["recall_at_50", "coverage_at_50", "novelty_at_50"],
        "data_quality": transaction_quality_report(transactions),
        "performance": {
            "validation_feature_seconds": validation_feature_seconds,
            "ranker_train_seconds": train_seconds,
            "test_feature_seconds": test_feature_seconds,
            "ranker_inference_seconds": inference_seconds,
            "ranker_model_size_bytes": ranker.serialized_size_bytes(),
            "peak_rss_mb": _peak_rss_mb(),
        },
        "candidate_sources": {
            name: evaluate_rankings(ranking, target, catalog, counts, config.k_values)
            for name, ranking in source_rankings.items()
        },
        "ranker": evaluate_rankings(ranked, target, catalog, counts, config.k_values),
    }
    config.artifacts_dir.mkdir(parents=True, exist_ok=True)
    path = config.artifacts_dir / f"v2-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(
        json.dumps(report, indent=2, default=str, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def _feature_rows_for_period(
    transactions: pl.DataFrame,
    articles: pl.DataFrame,
    catalog: set[str],
    period: EvaluationPeriod,
    config: V2Config,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    history = history_before(transactions, period.cutoff)
    target = labels_between(transactions, period)
    popularity = fit_trending_popularity(history, config.popularity_window_days)
    als = fit_als(
        history,
        factors=config.als_factors,
        regularization=config.als_regularization,
        iterations=config.als_iterations,
        random_seed=config.random_seed,
        fallback=popularity,
    )
    pool = build_candidate_pool(
        history,
        list(target),
        popularity,
        als,
        fit_item_cooccurrence(
            history,
            period.cutoff,
            window_days=config.cooccurrence_window_days,
            max_items_per_user=config.cooccurrence_max_items_per_user,
            max_neighbours=config.cooccurrence_max_neighbours,
        ),
        per_source_limit=config.per_source_limit,
        available_items=catalog,
    )
    rows = build_point_in_time_features(history, pool, period.cutoff, articles)
    return rows, pool


def _source_rankings(pool: pl.DataFrame) -> dict[str, dict[str, list[str]]]:
    result: dict[str, dict[str, list[str]]] = {}
    for source, column in (
        ("popularity", "popularity_rank"),
        ("als", "als_rank"),
        ("cooccurrence", "cooccurrence_rank"),
    ):
        sorted_rows = pool.filter(pl.col(column).is_not_null()).sort(["user_id", column, "item_id"])
        result[source] = {
            str(user[0]): group.get_column("item_id").to_list()
            for user, group in sorted_rows.group_by("user_id", maintain_order=True)
        }
    union = pool.with_columns(
        pl.min_horizontal("popularity_rank", "als_rank", "cooccurrence_rank").alias("rank")
    ).sort(["user_id", "rank", "item_id"])
    result["union"] = {
        str(user[0]): group.get_column("item_id").to_list()
        for user, group in union.group_by("user_id", maintain_order=True)
    }
    return result


def _jsonable_config(config: V2Config) -> dict[str, object]:
    return {
        key: str(value) if isinstance(value, Path) else value
        for key, value in asdict(config).items()
    }


def _peak_rss_mb() -> float:
    """Return process peak RSS in MiB on macOS and Linux."""

    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value / (1024 * 1024) if sys.platform == "darwin" else value / 1024
