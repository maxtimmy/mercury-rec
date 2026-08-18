"""Reject files that must remain local before a commit or CI run."""

from __future__ import annotations

import subprocess
import sys

from mercury_rec.public_tree import is_forbidden


def tracked_paths() -> list[str]:
    """Return Git-tracked paths without interpreting shell output."""

    result = subprocess.run(
        ["git", "ls-files", "-z"], check=True, capture_output=True, text=False
    )
    return [path.decode() for path in result.stdout.split(b"\0") if path]


def main() -> int:
    forbidden = [path for path in tracked_paths() if is_forbidden(path)]
    if not forbidden:
        return 0

    print("Refusing to publish local-only files:", file=sys.stderr)
    print(*[f"- {path}" for path in forbidden], sep="\n", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
