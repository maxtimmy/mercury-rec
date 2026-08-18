"""Validate and normalize locally downloaded H&M data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mercury_rec.data import normalize_raw_dataset, validate_raw_dataset


def main() -> int:
    """Run validation only or write normalized Parquet tables."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw/h-and-m-personalized-fashion-recommendations"),
    )
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed/hm-v1"))
    parser.add_argument("--validate-only", action="store_true")
    arguments = parser.parse_args()
    manifest = (
        validate_raw_dataset(arguments.raw_dir)
        if arguments.validate_only
        else normalize_raw_dataset(arguments.raw_dir, arguments.processed_dir)
    )
    print(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
