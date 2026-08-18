from datetime import date
from pathlib import Path

import polars as pl
import pytest

from mercury_rec.data import (
    DataContractError,
    _find_archive_checksum,
    make_temporal_split,
    normalize_raw_dataset,
)


def test_normalize_writes_canonical_parquet(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "transactions_train.csv").write_text(
        "t_dat,customer_id,article_id,price,sales_channel_id\n2020-09-01,u1,1,10.5,1\n",
        encoding="utf-8",
    )
    (raw / "customers.csv").write_text("customer_id,age\nu1,30\n", encoding="utf-8")
    (raw / "articles.csv").write_text("article_id,product_type_no\n1,2\n", encoding="utf-8")

    manifest = normalize_raw_dataset(raw, tmp_path / "processed")

    transactions = pl.read_parquet(tmp_path / "processed" / "transactions.parquet")
    assert manifest.files["transactions_train.csv"] == 1
    assert transactions.to_dicts() == [
        {
            "event_date": date(2020, 9, 1),
            "user_id": "u1",
            "item_id": "1",
            "price": 10.5,
            "sales_channel_id": 1,
        }
    ]


def test_split_reserves_two_future_label_windows() -> None:
    transactions = pl.DataFrame(
        {"event_date": pl.date_range(date(2020, 1, 1), date(2020, 1, 31), eager=True)}
    )

    split = make_temporal_split(transactions, horizon_days=7)

    assert split.validation.cutoff == date(2020, 1, 18)
    assert split.validation.label_end == date(2020, 1, 25)
    assert split.test.cutoff == date(2020, 1, 25)
    assert split.test.label_end == date(2020, 2, 1)


def test_normalize_rejects_missing_contract_column(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "transactions_train.csv").write_text(
        "t_dat,customer_id\n2020-09-01,u1\n", encoding="utf-8"
    )
    (raw / "customers.csv").write_text("customer_id\nu1\n", encoding="utf-8")
    (raw / "articles.csv").write_text("article_id\n1\n", encoding="utf-8")

    with pytest.raises(DataContractError, match="article_id"):
        normalize_raw_dataset(raw, tmp_path / "processed")


def test_archive_checksum_changes_when_any_download_changes(tmp_path: Path) -> None:
    (tmp_path / "articles.csv.zip").write_bytes(b"articles")
    (tmp_path / "transactions_train.csv.zip").write_bytes(b"transactions")

    original_checksum = _find_archive_checksum(tmp_path)
    (tmp_path / "transactions_train.csv.zip").write_bytes(b"new-transactions")

    assert original_checksum is not None
    assert original_checksum != _find_archive_checksum(tmp_path)
