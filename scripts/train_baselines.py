"""Train reproducible V1 popularity and ALS baselines."""

from __future__ import annotations

import argparse
from pathlib import Path

from mercury_rec.baselines import load_baseline_config, run_baselines


def main() -> int:
    """Execute the configured V1 offline benchmark."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    arguments = parser.parse_args()
    artifact = run_baselines(load_baseline_config(arguments.config))
    print(f"Wrote benchmark artifact: {artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
