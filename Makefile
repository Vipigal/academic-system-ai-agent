VENV := .venv
BIN := $(VENV)/bin
export APP_DATABASE_URL ?= postgresql+asyncpg://api:api@127.0.0.1:5432/cruzeiro
export APP_ORACLE_DATABASE_URL ?= postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/cruzeiro

MODEL ?= gpt-6-luna
EFFORT ?= low
SUITES ?= quality security protocol scope
SPLITS ?= dev
EPOCHS ?= 1
BATCH ?= 10
CONCURRENCY ?=
ENV_FILE ?= .env
RESULTS := src/evals/results
RUN_ID := $(shell date +%Y%m%d-%H%M)
OUT ?= $(RESULTS)/rodada-$(RUN_ID)

EVAL_RUN = $(BIN)/python -m evals.run --env-file $(ENV_FILE) --model $(MODEL) --effort $(EFFORT) \
	--suite $(SUITES) --split $(SPLITS) --epochs $(EPOCHS) --output $(OUT) \
	$(if $(CONCURRENCY),--concurrency $(CONCURRENCY))
EVAL_JUDGE = $(BIN)/python -m evals.judge --run-dir $(OUT) --batch-size $(BATCH)

.PHONY: setup check check-fast lint types test test-fast fix
.PHONY: eval eval-db eval-run eval-judge eval-calibrate eval-dashboard

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

eval: eval-db
	@echo "Rodada em $(OUT)"
	@$(EVAL_RUN); status=$$?; \
	if [ $$status -ge 2 ]; then \
		echo "Rodada incompleta (exit $$status). Retome com: make eval OUT=$(OUT)"; exit $$status; \
	fi; \
	$(EVAL_JUDGE) || { echo "Juiz incompleto. Retome com: make eval-judge OUT=$(OUT)"; exit 2; }; \
	echo "Painel: $(RESULTS)/index.html  Relatório: $(OUT)/report.md"; \
	if [ $$status -eq 1 ]; then echo "Gate reprovado: veja os itens críticos no relatório"; fi; \
	exit $$status

eval-db:
	docker compose up -d --wait db

eval-run: eval-db
	$(EVAL_RUN)

eval-judge:
	$(EVAL_JUDGE)

eval-calibrate:
	$(BIN)/python -m evals.calibration --output $(OUT) --batch-size $(BATCH)

eval-dashboard:
	$(BIN)/python -m evals.dashboard
