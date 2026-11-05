import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BLOCKING_EXIT_CODE = 2
RUFF_CONFIG = str(PROJECT_ROOT / "ruff.toml")
FLAKE8_CONFIG = str(PROJECT_ROOT / ".flake8")


class EditedFileLinter:
    def __init__(self, bin_dir: Path) -> None:
        self._bin_dir = bin_dir

    def lint(self, file_path: str) -> str:
        path = Path(file_path).resolve()
        if path.suffix != ".py" or not path.is_relative_to(PROJECT_ROOT):
            return ""
        reports = [self._run(command, path) for command in self._commands(path)]
        return "".join(reports)

    def _commands(self, path: Path) -> list[list[str]]:
        target = str(path)
        return [
            [str(self._bin_dir / "ruff"), "format", "--config", RUFF_CONFIG, "--check", target],
            [str(self._bin_dir / "ruff"), "check", "--config", RUFF_CONFIG, target],
            [str(self._bin_dir / "flake8"), "--config", FLAKE8_CONFIG, target],
            [str(self._bin_dir / "pyright"), target],
            [str(self._bin_dir / "python"), "-m", "tools.quality", target],
        ]

    @staticmethod
    def _run(command: list[str], path: Path) -> str:
        completed = subprocess.run(
            command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False
        )
        if completed.returncode == 0:
            return ""
        return f"{path.name} reprovado por {Path(command[0]).name}:\n{completed.stdout}"


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    edited_path = payload.get("tool_input", {}).get("file_path", "")
    report = EditedFileLinter(Path(sys.executable).parent).lint(edited_path)
    if report:
        sys.stderr.write(f"{report}Corrija no código; `make fix` resolve a formatação.\n")
        sys.exit(BLOCKING_EXIT_CODE)
