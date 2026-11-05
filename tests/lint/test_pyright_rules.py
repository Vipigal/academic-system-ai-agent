import json
from pathlib import Path

import pytest

from tests.lint.support import ToolRunner

DEPRECATED_LIFESPAN = """
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    yield
"""

CURRENT_LIFESPAN = """
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan() -> AsyncGenerator[None]:
    yield
"""

INCOMPATIBLE_OVERRIDE = """
class Base:
    def load(self, key: str) -> str:
        return key


class Child(Base):
    def load(self, key: int) -> str:
        return str(key)
"""


def pyright_rules(project: Path, source: str) -> set[str]:
    sample = project / "sample.py"
    sample.write_text(source, encoding="utf-8")
    completed = ToolRunner.run(["pyright", "--outputjson", str(sample)])
    diagnostics = json.loads(completed.stdout)["generalDiagnostics"]
    return {diagnostic.get("rule", "") for diagnostic in diagnostics}


@pytest.mark.parametrize(
    ("rule", "source"),
    [
        pytest.param("reportDeprecated", DEPRECATED_LIFESPAN, id="deprecated-as-error"),
        pytest.param("reportAssignmentType", 'value: int = "a"\n', id="wrong-assignment"),
        pytest.param(
            "reportIncompatibleMethodOverride", INCOMPATIBLE_OVERRIDE, id="standard-not-basic"
        ),
    ],
)
def test_flags_type_violation(tmp_path: Path, rule: str, source: str) -> None:
    assert rule in pyright_rules(tmp_path, source)


def test_accepts_current_lifespan_signature(tmp_path: Path) -> None:
    assert pyright_rules(tmp_path, CURRENT_LIFESPAN) == set()
