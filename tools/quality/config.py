import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Self

CONFIG_PATH = Path(__file__).resolve().parents[2] / "quality.toml"


@dataclass(frozen=True, slots=True)
class QualityConfig:
    function_lines: int
    class_lines: int
    module_lines: int
    docstring_allowed_paths: tuple[str, ...]
    domain_paths: tuple[str, ...]
    domain_package: str
    domain_allowed_stdlib: frozenset[str]
    examiner_marker: str
    session_access_module: str
    session_access_scope: tuple[str, ...]
    session_access_allowed: tuple[str, ...]
    per_file_ignores: dict[str, list[str]]

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> Self:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        limits = raw["limits"]
        return cls(
            function_lines=limits["function_lines"],
            class_lines=limits["class_lines"],
            module_lines=limits["module_lines"],
            docstring_allowed_paths=tuple(raw["docstring_allowed_paths"]),
            domain_paths=tuple(raw["domain_paths"]),
            domain_package=raw["domain_package"],
            domain_allowed_stdlib=frozenset(raw["domain_allowed_stdlib"]),
            examiner_marker=raw["examiner_marker"],
            session_access_module=raw["session_access_module"],
            session_access_scope=tuple(raw["session_access_scope"]),
            session_access_allowed=tuple(raw["session_access_allowed"]),
            per_file_ignores=raw["per_file_ignores"],
        )

    def is_ignored(self, code: str, path: PurePosixPath) -> bool:
        return any(
            code in codes and path.full_match(pattern)
            for pattern, codes in self.per_file_ignores.items()
        )
