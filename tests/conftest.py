from pathlib import Path

import pytest

TESTS_ROOT = Path(__file__).parent
FOLDER_MARKERS = {"unit": "unit", "integration": "integration", "e2e": "integration"}
LIVE_OPTION = "--live"
SKIP_LIVE = pytest.mark.skip(reason="chama o provedor de LLM: rode com --live")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        LIVE_OPTION,
        action="store_true",
        default=False,
        help="roda também os testes marcados live, que chamam o provedor de LLM",
    )


def folder_marker(item: pytest.Item) -> str | None:
    if not item.path.is_relative_to(TESTS_ROOT):
        return None
    return FOLDER_MARKERS.get(item.path.relative_to(TESTS_ROOT).parts[0])


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    run_live = bool(config.getoption(LIVE_OPTION))
    for item in items:
        marker = folder_marker(item)
        if marker:
            item.add_marker(marker)
        if not run_live and "live" in item.keywords:
            item.add_marker(SKIP_LIVE)
