.DEFAULT_GOAL := help

.PHONY: help install lint typecheck test check run compose-up compose-down audit-public

help:
	@printf '%s\n' 'Targets: install lint typecheck test check run compose-up compose-down audit-public'

install:
	uv sync --all-groups
	uv run pre-commit install

lint:
	uv run ruff check src tests scripts

typecheck:
	uv run mypy src tests scripts

test:
	uv run pytest

audit-public:
	uv run python scripts/verify_public_tree.py

check: audit-public lint typecheck test

run:
	uv run uvicorn mercury_rec.api:app --host 0.0.0.0 --port 8000 --reload

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down --remove-orphans
