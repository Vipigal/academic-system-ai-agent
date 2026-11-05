VENV := .venv
BIN := $(VENV)/bin
export APP_DATABASE_URL ?= postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/cruzeiro

.PHONY: setup check lint types test fix

setup:
	python3.14 -m venv $(VENV)
	$(BIN)/pip install --quiet --upgrade pip
	$(BIN)/pip install --quiet --group dev --editable .

check: lint types test

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
	$(BIN)/pytest

fix:
	$(BIN)/ruff check --config ruff.toml --fix .
	$(BIN)/ruff format --config ruff.toml .
