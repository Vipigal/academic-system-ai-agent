from dataclasses import replace
from pathlib import PurePosixPath

import pytest

from tools.quality.checker import SourceChecker
from tools.quality.config import QualityConfig

CONFIG = QualityConfig.load()


def codes_of(source: str, path: str = "src/api/application/sample.py") -> list[str]:
    violations = SourceChecker(CONFIG).check(source, PurePosixPath(path))
    return [violation.code for violation in violations]


def lines_of_code(count: int) -> str:
    return "".join(f"value_{number} = {number}\n" for number in range(count))


def function_with_lines(total_lines: int) -> str:
    body = "".join(f"    value_{number} = {number}\n" for number in range(total_lines - 1))
    return f"def build() -> None:\n{body}"


def class_with_lines(total_lines: int) -> str:
    body = "".join(f"    value_{number} = {number}\n" for number in range(total_lines - 1))
    return f"class Sample:\n{body}"


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("# explica o óbvio\nvalue = 1\n", id="own-line"),
        pytest.param("value = 1  # explica o óbvio\n", id="trailing"),
        pytest.param("import json  # noqa: F401\n", id="noqa"),
        pytest.param('value: int = "a"  # type: ignore[assignment]\n', id="type-ignore"),
        pytest.param("# ruff: noqa\n", id="ruff-file-noqa"),
        pytest.param("# fmt: off\n", id="formatter-off"),
        pytest.param("value = 1  # examiner: decisão # noqa: F841\n", id="marker-hiding-noqa"),
        pytest.param("value = 1  # examiner:\n", id="marker-without-text"),
    ],
)
def test_rejects_comment(source: str) -> None:
    assert "QA001" in codes_of(source)


def test_accepts_examiner_comment() -> None:
    assert codes_of("# examiner: o ownership é aplicado aqui\nvalue = 1\n") == []


def test_accepts_hash_inside_string() -> None:
    assert codes_of('value = "# não é comentário"\n') == []


@pytest.mark.parametrize(
    "source",
    [
        pytest.param('"""Módulo."""\n', id="module"),
        pytest.param('def build() -> None:\n    """Constrói."""\n', id="function"),
        pytest.param('class Sample:\n    """Amostra."""\n', id="class"),
        pytest.param('value = 1\n"""comentário disfarçado"""\n', id="loose-string"),
        pytest.param('b"""comentario em bytes"""\n', id="loose-bytes"),
        pytest.param('_ = """comentário atribuído"""\n', id="discarded-string"),
    ],
)
def test_rejects_docstring(source: str) -> None:
    assert "QA002" in codes_of(source)


def test_accepts_docstring_in_agent_tools() -> None:
    source = 'def list_invoices() -> None:\n    """Lista as faturas do aluno."""\n'
    assert codes_of(source, "src/api/application/agent/tools/finance.py") == []


@pytest.mark.parametrize(
    ("code", "above_limit", "at_limit"),
    [
        pytest.param("QA003", function_with_lines(31), function_with_lines(30), id="function"),
        pytest.param("QA004", class_with_lines(151), class_with_lines(150), id="class"),
        pytest.param("QA005", lines_of_code(301), lines_of_code(300), id="module"),
    ],
)
def test_enforces_size_limit(code: str, above_limit: str, at_limit: str) -> None:
    assert code in codes_of(above_limit)
    assert code not in codes_of(at_limit)


def test_counts_async_functions() -> None:
    source = function_with_lines(31).replace("def build", "async def build")
    assert "QA003" in codes_of(source)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("import sqlalchemy\n", id="third-party"),
        pytest.param("from pydantic import BaseModel\n", id="pydantic"),
        pytest.param("import api.persistence\n", id="outer-layer"),
        pytest.param("from api import application\n", id="outer-layer-from-root"),
        pytest.param("import socket\n", id="stdlib-network"),
        pytest.param("from urllib import request\n", id="stdlib-http"),
        pytest.param("import os\n", id="stdlib-environment"),
        pytest.param("if True:\n    import httpx\n", id="nested-import"),
        pytest.param("import asyncio\n", id="stdlib-event-loop"),
        pytest.param("import smtplib\n", id="stdlib-mail"),
    ],
)
def test_rejects_domain_import(source: str) -> None:
    assert "QA006" in codes_of(source, "src/api/domain/finance/invoice.py")


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("from dataclasses import dataclass\n", id="stdlib"),
        pytest.param("from __future__ import annotations\n", id="future"),
        pytest.param("from api.domain.brand import Brand\n", id="same-layer"),
    ],
)
def test_accepts_domain_import(source: str) -> None:
    assert codes_of(source, "src/api/domain/finance/invoice.py") == []


@pytest.mark.parametrize(
    "path",
    [
        "src/api/persistence/finance/repositories.py",
        "src/api/persistence/sag/repositories.py",
        "src/api/application/finance/service.py",
    ],
)
def test_rejects_opening_database_session_outside_the_adapter(path: str) -> None:
    assert "QA007" in codes_of("from sqlalchemy.ext.asyncio import AsyncSession\n", path)


@pytest.mark.parametrize(
    "path",
    [
        "src/api/persistence/core/database.py",
        "src/api/persistence/core/repository_adapter.py",
        "src/api/persistence/identity/student_session_repository.py",
        "tests/integration/conftest.py",
    ],
)
def test_accepts_database_session_in_its_owners(path: str) -> None:
    assert "QA007" not in codes_of("from sqlalchemy.ext.asyncio import AsyncSession\n", path)


@pytest.mark.parametrize(
    "path",
    [
        "src/api/domain/finance/invoice.py",
        "src/api/application/finance/service.py",
        "tools/quality/rules.py",
    ],
)
def test_rejects_dynamic_import_anywhere(path: str) -> None:
    assert "QA008" in codes_of('__import__("sqlalchemy")\n', path)


def test_outer_layers_may_import_third_party() -> None:
    assert codes_of("import sqlalchemy\n", "src/api/persistence/core/database.py") == []


def test_reports_syntax_error_instead_of_crashing() -> None:
    assert codes_of("def broken(:\n") == ["QA000"]


def test_message_tells_how_to_fix() -> None:
    violations = SourceChecker(CONFIG).check("value = 1  # c\n", PurePosixPath("src/api/a.py"))
    rendered = violations[0].render()
    assert rendered.startswith("src/api/a.py:1: QA001")
    assert "nomes e testes" in rendered


def test_per_file_ignore_comes_from_configuration() -> None:
    config = replace(CONFIG, per_file_ignores={"src/api/legacy/*": ["QA001"]})
    violations = SourceChecker(config).check(
        "value = 1  # c\n", PurePosixPath("src/api/legacy/a.py")
    )
    assert violations == []
