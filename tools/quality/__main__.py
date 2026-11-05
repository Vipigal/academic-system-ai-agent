import sys
from collections.abc import Iterator
from pathlib import Path, PurePosixPath

from tools.quality.checker import SourceChecker
from tools.quality.config import QualityConfig
from tools.quality.rules import Violation


class QualityCli:
    def __init__(self, checker: SourceChecker, root: Path) -> None:
        self._checker = checker
        self._root = root

    def run(self, arguments: list[str]) -> int:
        violations = [
            violation
            for path in self._python_files(arguments)
            for violation in self._check_file(path)
        ]
        for violation in violations:
            sys.stdout.write(f"{violation.render()}\n")
        return 1 if violations else 0

    @staticmethod
    def _python_files(arguments: list[str]) -> Iterator[Path]:
        for argument in arguments:
            path = Path(argument).resolve()
            yield from sorted(path.rglob("*.py")) if path.is_dir() else [path]

    def _check_file(self, path: Path) -> list[Violation]:
        relative_path = PurePosixPath(path.relative_to(self._root).as_posix())
        return self._checker.check(path.read_text(encoding="utf-8"), relative_path)


if __name__ == "__main__":
    cli = QualityCli(SourceChecker(QualityConfig.load()), Path.cwd())
    sys.exit(cli.run(sys.argv[1:]))
