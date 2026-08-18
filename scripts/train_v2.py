"""Run the leakage-safe V2 candidate and LambdaMART benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

from mercury_rec.v2 import load_v2_config, run_v2_benchmark


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    arguments = parser.parse_args()
    print(f"Wrote V2 benchmark artifact: {run_v2_benchmark(load_v2_config(arguments.config))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
