import ast
from collections.abc import Iterator

from tools.quality.config import QualityConfig
from tools.quality.rules import SourceFile, Violation

DYNAMIC_IMPORT_NAME = "__import__"


class ImportedModules:
    @staticmethod
    def of(source: SourceFile) -> Iterator[tuple[int, str]]:
        for node in ast.walk(source.tree):
            if isinstance(node, ast.Import):
                yield from ((node.lineno, alias.name) for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                yield node.lineno, node.module or ""


class DomainImportRule:
    MESSAGE = (
        "o domínio não depende de ninguém: `{module}` não pode entrar aqui. Declare uma "
        "interface em domain/ports.py e implemente na persistence."
    )

    def __init__(self, config: QualityConfig) -> None:
        self._paths = config.domain_paths
        self._package = config.domain_package
        self._allowed_stdlib = config.domain_allowed_stdlib

    def check(self, source: SourceFile) -> Iterator[Violation]:
        if not source.matches(self._paths):
            return
        for line, module in ImportedModules.of(source):
            if not self._is_allowed(module):
                yield source.violation(line, "QA006", self.MESSAGE.format(module=module))

    def _is_allowed(self, module: str) -> bool:
        is_same_layer = module == self._package or module.startswith(f"{self._package}.")
        return is_same_layer or module.partition(".")[0] in self._allowed_stdlib


class DynamicImportRule:
    MESSAGE = "import dinâmico esconde dependências das regras de camada. Use import explícito."

    def check(self, source: SourceFile) -> Iterator[Violation]:
        for node in ast.walk(source.tree):
            if isinstance(node, ast.Name) and node.id == DYNAMIC_IMPORT_NAME:
                yield source.violation(node.lineno, "QA008", self.MESSAGE)


class SessionAccessRule:
    MESSAGE = (
        "só o adapter e a carga da sessão abrem sessão de banco: `{module}` não pode entrar aqui. "
        "Consulte por RepositoryAdapter.fetch, que acrescenta o ownership."
    )

    def __init__(self, config: QualityConfig) -> None:
        self._module = config.session_access_module
        self._scope = config.session_access_scope
        self._allowed = config.session_access_allowed

    def check(self, source: SourceFile) -> Iterator[Violation]:
        if not source.matches(self._scope) or source.matches(self._allowed):
            return
        for line, module in ImportedModules.of(source):
            if module.startswith(self._module):
                message = self.MESSAGE.format(module=module)
                yield source.violation(line, "QA007", message)
