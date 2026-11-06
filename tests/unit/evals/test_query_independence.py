import ast
from pathlib import Path

import evals.oracle_queries

QUERIES_PACKAGE = Path(evals.oracle_queries.__file__).parent


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)} | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }


def test_named_queries_do_not_import_tools_services_or_the_api() -> None:
    imports = {module for path in QUERIES_PACKAGE.glob("*.py") for module in imported_modules(path)}
    assert {module for module in imports if not module.startswith("evals.oracle_queries")} == set()
