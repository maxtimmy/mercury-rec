from mercury_rec.public_tree import is_forbidden


def test_forbidden_ai_and_secret_paths_are_detected() -> None:
    assert is_forbidden(".codex/session.json")
    assert is_forbidden("AGENTS.md")
    assert is_forbidden(".env.production")
    assert is_forbidden("notes/design.prompt.md")


def test_normal_project_files_are_allowed() -> None:
    assert not is_forbidden("docs/architecture.md")
    assert not is_forbidden("src/mercury_rec/api.py")
    assert not is_forbidden(".env.example")
