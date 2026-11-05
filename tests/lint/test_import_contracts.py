import os
from pathlib import Path

import pytest

from tests.lint.support import PROJECT_ROOT, ToolRunner

LAYER_MODULES = (
    "api/__init__.py",
    "api/main.py",
    "api/settings.py",
    "api/presentation/__init__.py",
    "api/application/__init__.py",
    "api/persistence/__init__.py",
    "api/domain/__init__.py",
)


def contracts_result(project: Path, module: str, source: str) -> tuple[int, str]:
    for relative_path in LAYER_MODULES:
        target = project / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
    (project / module).write_text(source, encoding="utf-8")
    completed = ToolRunner.run(
        ["lint-imports", "--config", str(PROJECT_ROOT / ".importlinter"), "--no-cache"],
        cwd=project,
        env={**os.environ, "PYTHONPATH": str(project)},
    )
    return completed.returncode, completed.stdout


@pytest.mark.parametrize(
    ("module", "source", "broken_contract"),
    [
        pytest.param(
            "api/domain/invoice.py",
            "import api.persistence\n",
            "Camadas",
            id="domain-imports-persistence",
        ),
        pytest.param(
            "api/application/service.py",
            "import api.persistence\n",
            "Camadas",
            id="application-imports-persistence",
        ),
        pytest.param(
            "api/persistence/repo.py",
            "import api.application\n",
            "Camadas",
            id="persistence-imports-application",
        ),
        pytest.param(
            "api/presentation/route.py",
            "import api.persistence\n",
            "Presentation",
            id="presentation-imports-persistence",
        ),
        pytest.param(
            "api/application/service.py",
            "import sqlalchemy\n",
            "Apenas a persistence",
            id="application-imports-sqlalchemy",
        ),
        pytest.param(
            "api/presentation/route.py",
            "import asyncpg\n",
            "Apenas a persistence",
            id="presentation-imports-asyncpg",
        ),
        pytest.param(
            "api/application/service.py",
            "import fastapi\n",
            "HTTP",
            id="application-imports-fastapi",
        ),
        pytest.param(
            "api/persistence/repo.py",
            "import pydantic_ai\n",
            "Framework do agente",
            id="persistence-imports-agent-framework",
        ),
    ],
)
def test_breaks_contract(tmp_path: Path, module: str, source: str, broken_contract: str) -> None:
    return_code, output = contracts_result(tmp_path, module, source)
    assert return_code == 1, output
    broken_lines = [line for line in output.splitlines() if "BROKEN" in line]
    assert any(broken_contract in line for line in broken_lines), output


@pytest.mark.parametrize(
    ("module", "source"),
    [
        pytest.param(
            "api/presentation/route.py", "import api.application\n", id="presentation-down"
        ),
        pytest.param("api/application/service.py", "import api.domain\n", id="application-down"),
        pytest.param("api/persistence/repo.py", "import api.domain\n", id="persistence-down"),
        pytest.param("api/persistence/repo.py", "import sqlalchemy\n", id="persistence-sqlalchemy"),
        pytest.param("api/presentation/route.py", "import fastapi\n", id="presentation-fastapi"),
        pytest.param("api/main.py", "import api.persistence\n", id="composition-root"),
    ],
)
def test_keeps_contracts(tmp_path: Path, module: str, source: str) -> None:
    return_code, output = contracts_result(tmp_path, module, source)
    assert return_code == 0, output
