"""Download the H&M competition data through the user's local Kaggle credentials."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

COMPETITION = "h-and-m-personalized-fashion-recommendations"
DESTINATION = Path("data/raw") / COMPETITION
REQUIRED_FILES = ("transactions_train.csv", "customers.csv", "articles.csv")


def main() -> int:
    """Download and extract data without placing credentials or data in Git."""

    if shutil.which("kaggle") is None:
        print("Kaggle CLI is not installed. Run `uv sync --all-groups` first.", file=sys.stderr)
        return 1
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for filename in REQUIRED_FILES:
        command = [
            "kaggle",
            "competitions",
            "download",
            COMPETITION,
            "--file",
            filename,
            "--path",
            str(DESTINATION),
        ]
        result = subprocess.run(command, check=False)
        if result.returncode:
            print(
                "Kaggle download failed. Confirm the token and competition rules at Kaggle.",
                file=sys.stderr,
            )
            return result.returncode
        archive = DESTINATION / f"{filename}.zip"
        if archive.is_file():
            with ZipFile(archive) as zip_file:
                zip_file.extractall(DESTINATION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
