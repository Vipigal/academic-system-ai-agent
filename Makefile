VENV := .venv
BIN := $(VENV)/bin
export APP_DATABASE_URL ?= postgresql+asyncpg://api:api@127.0.0.1:5432/cruzeiro
export APP_ORACLE_DATABASE_URL ?= postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/cruzeiro

.PHONY: setup check check-fast lint types test test-fast fix

setup:
	uv sync --python 3.14 --group dev

check: lint types test

check-fast: lint types test-fast

lint:
	$(BIN)/ruff format --config ruff.toml --check .
	$(BIN)/ruff check --config ruff.toml .
	$(BIN)/flake8 --config .flake8 src tools tests
	$(BIN)/lint-imports --config .importlinter
	$(BIN)/python -m tools.quality src tools tests

types:
	$(BIN)/mypy --config-file mypy.ini
	$(BIN)/pyright

test:
	$(BIN)/pytest -n 4 --dist loadfile --cov --cov-report=term-missing:skip-covered

test-fast:
	$(BIN)/pytest -n 4 --dist loadfile -m "not sweep and not slow" --ignore=tests/lint

fix:
	$(BIN)/ruff check --config ruff.toml --fix .
	$(BIN)/ruff format --config ruff.toml .
