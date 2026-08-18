"""Rules that keep local-only files out of the public repository."""

from pathlib import PurePosixPath

FORBIDDEN_EXACT = {
    ".env",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "AI_INSTRUCTIONS.md",
    ".github/copilot-instructions.md",
}
FORBIDDEN_PREFIXES = (
    ".agents/",
    ".codex/",
    ".cursor/",
    ".continue/",
    ".roo/",
    ".windsurf/",
    "data/",
    "artifacts/",
    "mlruns/",
)


def is_forbidden(path: str) -> bool:
    """Return whether a repository path may not be published."""

    normalized = PurePosixPath(path).as_posix()
    return (
        normalized in FORBIDDEN_EXACT
        or normalized.startswith(FORBIDDEN_PREFIXES)
        or normalized.endswith(".prompt.md")
        or (normalized.startswith(".env.") and normalized != ".env.example")
    )
