import ast
import io
import tokenize
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import PurePosixPath

from tools.quality.config import QualityConfig

DISCARD_NAME = "_"


@dataclass(frozen=True, slots=True)
class Violation:
    path: PurePosixPath
    line: int
    code: str
    message: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message}"


@dataclass(frozen=True, slots=True)
class SourceFile:
    path: PurePosixPath
    text: str
    tree: ast.Module

    def violation(self, line: int, code: str, message: str) -> Violation:
        return Violation(self.path, line, code, message)

    def matches(self, patterns: tuple[str, ...]) -> bool:
        return any(self.path.full_match(pattern) for pattern in patterns)


class CommentRule:
    MESSAGE = (
        "comentário proibido, inclusive noqa e type: ignore. Explique com nomes e testes; "
        "exceção a uma regra vai na configuração do linter, onde o review enxerga."
    )

    def __init__(self, config: QualityConfig) -> None:
        self._marker = config.examiner_marker

    def check(self, source: SourceFile) -> Iterator[Violation]:
        for token in tokenize.generate_tokens(io.StringIO(source.text).readline):
            if token.type == tokenize.COMMENT and not self._is_examiner_note(token.string):
                yield source.violation(token.start[0], "QA001", self.MESSAGE)

    def _is_examiner_note(self, comment: str) -> bool:
        text = comment.removeprefix("#").strip()
        note = text.removeprefix(self._marker).strip()
        return text.startswith(self._marker) and bool(note) and "#" not in note


class DocstringRule:
    MESSAGE = (
        "docstring ou string solta proibida. Só as tools do agente usam docstring, porque o "
        "modelo a lê como descrição; no resto, explique com nomes e testes."
    )

    def __init__(self, config: QualityConfig) -> None:
        self._allowed_paths = config.docstring_allowed_paths

    def check(self, source: SourceFile) -> Iterator[Violation]:
        if source.matches(self._allowed_paths):
            return
        for node in ast.walk(source.tree):
            if isinstance(node, ast.Expr | ast.Assign) and self._is_loose_text(node):
                yield source.violation(node.lineno, "QA002", self.MESSAGE)

    @classmethod
    def _is_loose_text(cls, node: ast.Expr | ast.Assign) -> bool:
        if isinstance(node, ast.Expr):
            return cls._is_text(node.value)
        return cls._is_text(node.value) and all(
            isinstance(target, ast.Name) and target.id == DISCARD_NAME for target in node.targets
        )

    @staticmethod
    def _is_text(value: ast.expr) -> bool:
        return isinstance(value, ast.Constant) and isinstance(value.value, str | bytes)


@dataclass(frozen=True, slots=True)
class SizeLimit:
    code: str
    limit: int
    how_to_fix: str

    def violation_of(self, source: SourceFile, subject: str, line: int, size: int) -> Violation:
        message = f"{subject} tem {size} linhas (limite {self.limit}). {self.how_to_fix}"
        return source.violation(line, self.code, message)


class SizeRule:
    def __init__(self, config: QualityConfig) -> None:
        self._function = SizeLimit(
            "QA003", config.function_lines, "Extraia passos com nomes de negócio."
        )
        self._class = SizeLimit(
            "QA004", config.class_lines, "Separe as responsabilidades em classes menores."
        )
        self._module = SizeLimit(
            "QA005", config.module_lines, "Divida o módulo por responsabilidade."
        )

    def check(self, source: SourceFile) -> Iterator[Violation]:
        module_size = len(source.text.splitlines())
        if module_size > self._module.limit:
            yield self._module.violation_of(source, "módulo", 1, module_size)
        for node in ast.walk(source.tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                yield from self._check_node(source, node, self._function)
            elif isinstance(node, ast.ClassDef):
                yield from self._check_node(source, node, self._class)

    @staticmethod
    def _check_node(
        source: SourceFile,
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
        limit: SizeLimit,
    ) -> Iterator[Violation]:
        size = (node.end_lineno or node.lineno) - node.lineno + 1
        if size > limit.limit:
            yield limit.violation_of(source, f"`{node.name}`", node.lineno, size)
