from datetime import date, timedelta
from pathlib import Path

import polars as pl

from mercury_rec.baselines import BaselineConfig, run_baselines


def test_baselines_write_validation_and_test_artifact(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    processed.mkdir()
    rows: list[dict[str, object]] = []
    for day_offset in range(35):
        event_date = date(2020, 1, 1) + timedelta(days=day_offset)
        for user_id, item_id in (("u1", "a"), ("u2", "b"), ("u3", "c")):
            rows.append(
                {
                    "event_date": event_date,
                    "user_id": user_id,
                    "item_id": item_id,
                    "price": 10.0,
                    "sales_channel_id": 1,
                }
            )
    pl.DataFrame(rows).write_parquet(processed / "transactions.parquet")
    pl.DataFrame({"item_id": ["a", "b", "c"]}).write_parquet(processed / "articles.parquet")
    config = BaselineConfig(
        raw_dir=tmp_path / "raw",
        processed_dir=processed,
        artifacts_dir=tmp_path / "artifacts",
        horizon_days=7,
        popularity_window_days=7,
        recommendation_limit=3,
        als_factors=2,
        als_regularization=0.05,
        als_iterations=1,
        als_random_seed=42,
        k_values=[2],
    )

    artifact = run_baselines(config)

    report = artifact.read_text(encoding="utf-8")
    assert artifact.is_file()
    assert '"validation"' in report
    assert '"test"' in report
    assert '"recall_at_2"' in report
