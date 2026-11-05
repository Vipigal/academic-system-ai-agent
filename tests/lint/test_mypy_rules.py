from pathlib import Path

import pytest

from tests.lint.support import PROJECT_ROOT, ToolRunner

MODEL = """
from pydantic import BaseModel


class Invoice(BaseModel):
    number: int

"""


def mypy_output(project: Path, source: str) -> str:
    sample = project / "sample.py"
    sample.write_text(source, encoding="utf-8")
    completed = ToolRunner.run(
        [
            "mypy",
            "--config-file",
            str(PROJECT_ROOT / "mypy.ini"),
            "--cache-dir",
            str(project / ".mypy_cache"),
            str(sample),
        ],
        cwd=project,
    )
    assert completed.returncode in {0, 1}, completed.stdout + completed.stderr
    return completed.stdout


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(MODEL + 'Invoice(number="1")\n', "arg-type", id="pydantic-typed-init"),
        pytest.param(
            MODEL + "Invoice(number=1, extra=2)\n", "call-arg", id="pydantic-forbid-extra"
        ),
        pytest.param("def f(x):\n    return x\n", "no-untyped-def", id="strict-untyped-def"),
    ],
)
def test_flags_type_violation(tmp_path: Path, source: str, expected: str) -> None:
    assert expected in mypy_output(tmp_path, source)


def test_accepts_valid_pydantic_call(tmp_path: Path) -> None:
    assert "Success" in mypy_output(tmp_path, MODEL + "Invoice(number=1)\n")
