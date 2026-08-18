"""Download the H&M competition data through the user's local Kaggle credentials."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

COMPETITION = "h-and-m-personalized-fashion-recommendations"
DESTINATION = Path("data/raw") / COMPETITION


def main() -> int:
    """Download and extract data without placing credentials or data in Git."""

    if shutil.which("kaggle") is None:
        print("Kaggle CLI is not installed. Run `uv sync --all-groups` first.", file=sys.stderr)
        return 1
    DESTINATION.mkdir(parents=True, exist_ok=True)
    command = [
        "kaggle",
        "competitions",
        "download",
        "-c",
        COMPETITION,
        "-p",
        str(DESTINATION),
        "--unzip",
    ]
    result = subprocess.run(command, check=False)
    if result.returncode:
        print(
            "Kaggle download failed. Add a token at ~/.kaggle/kaggle.json "
            "and accept the competition rules.",
            file=sys.stderr,
        )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
