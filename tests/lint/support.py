import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = Path(sys.executable).parent


class ToolRunner:
    @staticmethod
    def run(
        command: list[str],
        *,
        stdin: str | None = None,
        cwd: Path = PROJECT_ROOT,
        env: Mapping[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(BIN_DIR / command[0]), *command[1:]],
            input=stdin,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )


class SampleCode:
    @staticmethod
    def numbered_branches(count: int) -> str:
        branches = "".join(
            f"    if value == {number}:\n        total += 1\n" for number in range(count)
        )
        return f"def choose(value: int) -> int:\n    total = 0\n{branches}    return total\n"

    @staticmethod
    def signature_with(count: int) -> str:
        names = ", ".join(f"arg{number}: int" for number in range(count))
        return f"def build(*, {names}) -> None:\n    return None\n"
