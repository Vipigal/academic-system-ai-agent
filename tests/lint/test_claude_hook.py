import json
import sys
import tempfile
from pathlib import Path

from tests.lint.support import PROJECT_ROOT, ToolRunner

BLOCKING_EXIT_CODE = 2


def run_hook(file_path: Path) -> tuple[int, str]:
    payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(file_path)}})
    completed = ToolRunner.run(
        [Path(sys.executable).name, "-m", "tools.quality.claude_hook"],
        stdin=payload,
        cwd=PROJECT_ROOT,
    )
    return completed.returncode, completed.stderr


def hook_result_for(source: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
        (Path(directory) / "__init__.py").touch()
        target = Path(directory) / "edited_sample.py"
        target.write_text(source, encoding="utf-8")
        return run_hook(target)


def test_blocks_file_with_violation_and_explains_it() -> None:
    return_code, feedback = hook_result_for('VALUE = 1  # explica\nprint("debug")\n')
    assert return_code == BLOCKING_EXIT_CODE
    assert "QA001" in feedback
    assert "print" in feedback


def test_blocks_deprecated_api_seen_only_by_pyright() -> None:
    source = (
        "from collections.abc import AsyncIterator\n"
        "from contextlib import asynccontextmanager\n\n\n"
        "@asynccontextmanager\n"
        "async def lifespan() -> AsyncIterator[None]:\n"
        "    yield\n"
    )
    return_code, feedback = hook_result_for(source)
    assert return_code == BLOCKING_EXIT_CODE
    assert "reportDeprecated" in feedback


def test_accepts_clean_file() -> None:
    assert hook_result_for("VALUE = 1\n") == (0, "")


def test_ignores_files_outside_the_project(tmp_path: Path) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text("value = 1  # c\n", encoding="utf-8")
    assert run_hook(outside) == (0, "")


def test_ignores_non_python_files(tmp_path: Path) -> None:
    assert run_hook(tmp_path / "notes.md") == (0, "")
