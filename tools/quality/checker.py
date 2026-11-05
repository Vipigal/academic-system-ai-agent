import ast
from pathlib import PurePosixPath

from tools.quality.config import QualityConfig
from tools.quality.import_rules import DomainImportRule, DynamicImportRule, SessionAccessRule
from tools.quality.rules import CommentRule, DocstringRule, SizeRule, SourceFile, Violation


class SourceChecker:
    def __init__(self, config: QualityConfig) -> None:
        self._config = config
        self._rules = (
            CommentRule(config),
            DocstringRule(config),
            SizeRule(config),
            DomainImportRule(config),
            DynamicImportRule(),
            SessionAccessRule(config),
        )

    def check(self, text: str, path: PurePosixPath) -> list[Violation]:
        try:
            tree = ast.parse(text)
        except SyntaxError as error:
            return [Violation(path, error.lineno or 1, "QA000", error.msg)]
        source = SourceFile(path, text, tree)
        found = [violation for rule in self._rules for violation in rule.check(source)]
        return [item for item in found if not self._config.is_ignored(item.code, path)]
