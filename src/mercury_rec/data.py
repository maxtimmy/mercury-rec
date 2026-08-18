"""H&M ingestion, validation, normalization, and temporal split utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from hashlib import sha256
from pathlib import Path

import polars as pl

REQUIRED_COLUMNS: dict[str, set[str]] = {
    "transactions_train.csv": {"t_dat", "customer_id", "article_id", "price", "sales_channel_id"},
    "customers.csv": {"customer_id"},
    "articles.csv": {"article_id"},
}


class DataContractError(ValueError):
    """Raised when source data violates the expected H&M contract."""


@dataclass(frozen=True)
class DatasetManifest:
    """Non-sensitive provenance metadata for a local data snapshot."""

    archive_sha256: str | None
    source: str
    files: dict[str, int]
    max_transaction_date: str
    min_transaction_date: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationPeriod:
    """History cutoff and the following label window."""

    name: str
    cutoff: date
    label_end: date


@dataclass(frozen=True)
class TemporalSplit:
    """Two leakage-safe evaluation periods derived from the observed maximum date."""

    validation: EvaluationPeriod
    test: EvaluationPeriod


def validate_raw_dataset(raw_dir: Path) -> DatasetManifest:
    """Validate required files/columns and return a local provenance summary."""

    file_counts: dict[str, int] = {}
    for filename, required in REQUIRED_COLUMNS.items():
        path = raw_dir / filename
        if not path.is_file():
            raise DataContractError(f"Missing required file: {path}")
        columns = set(pl.read_csv(path, n_rows=0).columns)
        missing = required - columns
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise DataContractError(f"{filename} is missing required columns: {missing_text}")
        file_counts[filename] = pl.scan_csv(path).select(pl.len()).collect().item()

    transaction_dates = (
        pl.scan_csv(raw_dir / "transactions_train.csv")
        .select(pl.col("t_dat").str.strptime(pl.Date, "%Y-%m-%d", strict=True).alias("event_date"))
        .collect()
        .get_column("event_date")
    )
    if transaction_dates.null_count() or transaction_dates.is_empty():
        raise DataContractError("transactions_train.csv has missing or invalid t_dat values")

    return DatasetManifest(
        archive_sha256=_find_archive_checksum(raw_dir),
        source="kaggle:h-and-m-personalized-fashion-recommendations",
        files=file_counts,
        min_transaction_date=str(transaction_dates.min()),
        max_transaction_date=str(transaction_dates.max()),
    )


def normalize_raw_dataset(raw_dir: Path, processed_dir: Path) -> DatasetManifest:
    """Write canonical Parquet tables without altering the raw Kaggle files."""

    manifest = validate_raw_dataset(raw_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    transactions = (
        pl.read_csv(raw_dir / "transactions_train.csv")
        .select(
            pl.col("t_dat").str.strptime(pl.Date, "%Y-%m-%d", strict=True).alias("event_date"),
            pl.col("customer_id").cast(pl.String).alias("user_id"),
            pl.col("article_id").cast(pl.String).alias("item_id"),
            pl.col("price").cast(pl.Float64),
            pl.col("sales_channel_id").cast(pl.Int8),
        )
        .drop_nulls(["event_date", "user_id", "item_id", "price"])
    )
    transactions.write_parquet(processed_dir / "transactions.parquet")

    pl.read_csv(raw_dir / "customers.csv").with_columns(
        pl.col("customer_id").cast(pl.String).alias("user_id")
    ).write_parquet(processed_dir / "customers.parquet")
    pl.read_csv(raw_dir / "articles.csv").with_columns(
        pl.col("article_id").cast(pl.String).alias("item_id")
    ).write_parquet(processed_dir / "articles.parquet")
    (processed_dir / "manifest.json").write_text(_manifest_json(manifest), encoding="utf-8")
    return manifest


def load_transactions(processed_dir: Path) -> pl.DataFrame:
    """Load normalized transactions with a stable schema."""

    path = processed_dir / "transactions.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"Normalized transactions do not exist: {path}")
    return pl.read_parquet(path)


def make_temporal_split(transactions: pl.DataFrame, horizon_days: int) -> TemporalSplit:
    """Reserve the final two contiguous horizons for validation and test labels."""

    if horizon_days < 1:
        raise ValueError("horizon_days must be positive")
    max_date = transactions.get_column("event_date").max()
    min_date = transactions.get_column("event_date").min()
    if not isinstance(max_date, date) or not isinstance(min_date, date):
        raise DataContractError("event_date must be a date column")
    test_cutoff = max_date - timedelta(days=horizon_days - 1)
    validation_cutoff = test_cutoff - timedelta(days=horizon_days)
    if validation_cutoff <= min_date:
        raise DataContractError("Not enough history for two temporal evaluation windows")
    return TemporalSplit(
        validation=EvaluationPeriod("validation", validation_cutoff, test_cutoff),
        test=EvaluationPeriod("test", test_cutoff, max_date + timedelta(days=1)),
    )


def history_before(transactions: pl.DataFrame, cutoff: date) -> pl.DataFrame:
    """Return interactions available at a given point in time."""

    return transactions.filter(pl.col("event_date") < pl.lit(cutoff))


def labels_between(transactions: pl.DataFrame, period: EvaluationPeriod) -> dict[str, set[str]]:
    """Return unique next-horizon purchases for users with at least one target."""

    labels = transactions.filter(
        (pl.col("event_date") >= pl.lit(period.cutoff))
        & (pl.col("event_date") < pl.lit(period.label_end))
    )
    grouped = labels.group_by("user_id").agg(pl.col("item_id").unique())
    return {
        row["user_id"]: set(row["item_id"])
        for row in grouped.iter_rows(named=True)
    }


def _find_archive_checksum(raw_dir: Path) -> str | None:
    archives = sorted(raw_dir.glob("*.zip"))
    if not archives:
        return None
    digest = sha256()
    with archives[0].open("rb") as archive:
        for chunk in iter(lambda: archive.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_json(manifest: DatasetManifest) -> str:
    import json

    return json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n"
