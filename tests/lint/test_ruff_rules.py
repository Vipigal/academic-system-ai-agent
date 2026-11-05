import json

import pytest

from tests.lint.support import PROJECT_ROOT, SampleCode, ToolRunner

NESTED_FOUR_LEVELS = """
def scan(rows: list[list[int]]) -> int:
    total = 0
    for row in rows:
        if row:
            for cell in row:
                if cell:
                    total += cell
    return total
"""

NESTED_THREE_LEVELS = """
def scan(rows: list[list[int]]) -> int:
    total = 0
    for row in rows:
        if row:
            for cell in row:
                total += cell
    return total
"""

ROUTE_WITHOUT_ANNOTATED = """
from fastapi import APIRouter, Depends

router = APIRouter()


def current_user() -> str:
    return "user"


@router.get("/items")
async def list_items(user: str = Depends(current_user)) -> list[str]:
    return [user]
"""

ROUTE_WITH_UNUSED_PATH_PARAMETER = """
from fastapi import APIRouter

router = APIRouter()


@router.get("/items/{item_id}")
async def read_item() -> list[str]:
    return []
"""


def ruff_codes(source: str, filename: str = "src/api/sample.py") -> set[str]:
    completed = ToolRunner.run(
        [
            "ruff",
            "check",
            "--config",
            str(PROJECT_ROOT / "ruff.toml"),
            "--output-format=json",
            "--no-cache",
            "--stdin-filename",
            str(PROJECT_ROOT / filename),
            "-",
        ],
        stdin=source,
    )
    assert completed.returncode in {0, 1}, completed.stderr
    return {finding["code"] for finding in json.loads(completed.stdout)}


@pytest.mark.parametrize(
    ("code", "source"),
    [
        pytest.param("PLR1702", NESTED_FOUR_LEVELS, id="nesting-above-limit"),
        pytest.param("PLR0913", SampleCode.signature_with(6), id="arguments-above-limit"),
        pytest.param("C901", SampleCode.numbered_branches(8), id="cyclomatic-above-limit"),
        pytest.param("E722", "try:\n    pass\nexcept:\n    pass\n", id="bare-except"),
        pytest.param("BLE001", "try:\n    pass\nexcept Exception:\n    pass\n", id="blind-except"),
        pytest.param("T201", 'print("debug")\n', id="print"),
        pytest.param(
            "ANN401", "from typing import Any\n\n\ndef f(x: Any) -> None: ...\n", id="any"
        ),
        pytest.param("PLR2004", "def f(x: int) -> bool:\n    return x > 42\n", id="magic-number"),
        pytest.param("B006", "def f(x: list[int] = []) -> None: ...\n", id="mutable-default"),
        pytest.param("F401", "import json\n", id="unused-import"),
        pytest.param("TID252", "from . import sibling\n\nsibling()\n", id="relative-import"),
        pytest.param("N818", "class Missing(Exception):\n    pass\n", id="exception-name"),
        pytest.param(
            "S608", 'def f(x: str) -> str:\n    return f"SELECT {x} FROM t"\n', id="sql-fstring"
        ),
        pytest.param("S105", 'password = "hunter2"\n', id="hardcoded-password"),
        pytest.param(
            "ASYNC251",
            "import time\n\n\nasync def f() -> None:\n    time.sleep(1)\n",
            id="blocking-sleep-in-async",
        ),
        pytest.param("FAST002", ROUTE_WITHOUT_ANNOTATED, id="fastapi-without-annotated"),
        pytest.param(
            "FAST003", ROUTE_WITH_UNUSED_PATH_PARAMETER, id="fastapi-unused-path-parameter"
        ),
    ],
)
def test_flags_violation(code: str, source: str) -> None:
    assert code in ruff_codes(source)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("from sqlalchemy.orm import relationship\n", id="relationship"),
        pytest.param("from sqlalchemy.orm import aliased\n", id="aliased"),
        pytest.param("from sqlalchemy.orm import Session\n", id="sync-session"),
        pytest.param("from sqlalchemy import text\n", id="text"),
        pytest.param("from sqlalchemy.sql import text\n", id="text-from-sql"),
        pytest.param("from sqlalchemy.sql.expression import text\n", id="text-from-expression"),
        pytest.param("from sqlalchemy.orm import Relationship\n", id="relationship-class"),
        pytest.param("from typing import Any\n", id="typing-any"),
        pytest.param("from typing import cast\n", id="typing-cast"),
        pytest.param("from typing import no_type_check\n", id="no-type-check"),
        pytest.param("from sqlalchemy import literal_column\n", id="literal-column"),
        pytest.param("from sqlalchemy import create_engine\n", id="sync-engine"),
        pytest.param("from os import getenv\n", id="getenv"),
        pytest.param("from os import environ\n", id="environ"),
        pytest.param("from importlib import import_module\n", id="dynamic-import"),
        pytest.param("from datetime import datetime\n\ndatetime.now()\n", id="clock-now"),
        pytest.param("from datetime import date\n\ndate.today()\n", id="clock-today"),
    ],
)
def test_bans_api_that_bypasses_the_architecture(source: str) -> None:
    assert "TID251" in ruff_codes(source)


@pytest.mark.parametrize(
    ("code", "source"),
    [
        pytest.param("PLR1702", NESTED_THREE_LEVELS, id="nesting-at-limit"),
        pytest.param("PLR0913", SampleCode.signature_with(5), id="arguments-at-limit"),
        pytest.param("C901", SampleCode.numbered_branches(7), id="cyclomatic-at-limit"),
    ],
)
def test_accepts_code_at_the_limit(code: str, source: str) -> None:
    assert code not in ruff_codes(source)


def test_allows_raw_sql_only_in_tests() -> None:
    source = "from sqlalchemy import text\n"
    assert "TID251" not in ruff_codes(source, "tests/integration/test_sample.py")
