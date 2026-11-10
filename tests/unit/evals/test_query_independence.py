import ast
from pathlib import Path

import evals.dataset.oracle

ORACLE_FILE = Path(evals.dataset.oracle.__file__)
FORBIDDEN_PREFIXES = ("api", "evals.graders", "evals.runner", "evals.student_driver")


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)} | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }


def test_the_oracle_does_not_import_tools_services_or_the_api() -> None:
    imports = imported_modules(ORACLE_FILE)
    assert {module for module in imports if module.startswith(FORBIDDEN_PREFIXES)} == set()
