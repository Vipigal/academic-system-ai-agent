import os
from pathlib import Path

import pytest

from tests.ephemeral_postgres import (
    SERVER_VARIABLE,
    TEMPLATE,
    EphemeralPostgres,
    clone_template,
    docker_answers,
    point_environment,
)

TESTS_ROOT = Path(__file__).parent
FOLDER_MARKERS = {"unit": "unit", "integration": "integration", "e2e": "integration"}
DATABASE_FREE_FOLDERS = ("unit", "lint")
LIVE_OPTION = "--live"
SKIP_LIVE = pytest.mark.skip(reason="chama o provedor de LLM: rode com --live")
DOCKER_MISSING = "Docker indisponível: testes de banco pulados"
DOCKER_REQUIRED = "Docker indisponível com CI definido: os testes de banco não podem ser pulados"
SKIP_DATABASE = pytest.mark.skip(reason=DOCKER_MISSING)
DATABASE_KEY = pytest.StashKey[EphemeralPostgres]()
STATUS_KEY = pytest.StashKey[str]()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        LIVE_OPTION,
        action="store_true",
        default=False,
        help="roda também os testes marcados live, que chamam o provedor de LLM",
    )


def pytest_configure(config: pytest.Config) -> None:
    workerinput = getattr(config, "workerinput", None)
    if workerinput is None:
        os.environ[SERVER_VARIABLE] = serve(config)
        point_environment(os.environ[SERVER_VARIABLE], TEMPLATE)
        return
    server = os.environ[SERVER_VARIABLE]
    if server:
        point_environment(server, clone_template(server, str(workerinput["workerid"])))


def serve(config: pytest.Config) -> str:
    if not docker_answers():
        if "CI" in os.environ:
            raise pytest.UsageError(DOCKER_REQUIRED)
        config.stash[STATUS_KEY] = DOCKER_MISSING
        return ""
    if not reaches_database_tests(config):
        config.stash[STATUS_KEY] = "banco de teste: nenhum teste de banco no escopo"
        return ""
    database = EphemeralPostgres()
    config.stash[DATABASE_KEY] = database
    server = database.start()
    config.stash[STATUS_KEY] = (
        f"banco de teste: Postgres efêmero carregado em {database.load_seconds:.1f}s"
    )
    return server


def reaches_database_tests(config: pytest.Config) -> bool:
    free = [TESTS_ROOT / folder for folder in DATABASE_FREE_FOLDERS]
    targets = [
        Path(config.invocation_params.dir, argument.split("::")[0]).resolve()
        for argument in config.args
    ]
    return not targets or not all(
        any(target.is_relative_to(folder) for folder in free) for target in targets
    )


def pytest_unconfigure(config: pytest.Config) -> None:
    database = config.stash.get(DATABASE_KEY, None)
    if database is not None:
        database.stop()


def pytest_report_header(config: pytest.Config) -> list[str]:
    status = config.stash.get(STATUS_KEY, None)
    return [status] if status else []


def folder_marker(item: pytest.Item) -> str | None:
    if not item.path.is_relative_to(TESTS_ROOT):
        return None
    return FOLDER_MARKERS.get(item.path.relative_to(TESTS_ROOT).parts[0])


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    run_live = bool(config.getoption(LIVE_OPTION))
    database_up = bool(os.environ[SERVER_VARIABLE])
    for item in items:
        marker = folder_marker(item)
        if marker:
            item.add_marker(marker)
        if marker == "integration" and not database_up:
            item.add_marker(SKIP_DATABASE)
        if not run_live and "live" in item.keywords:
            item.add_marker(SKIP_LIVE)
