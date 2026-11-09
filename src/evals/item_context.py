from dataclasses import dataclass, field
from typing import Self

from evals.golden.items import GoldenItem
from evals.graders.text import PlainText

SEARCHABLE_LENGTH = 6


@dataclass(frozen=True, slots=True)
class ForeignIdentifiers:
    raw: frozenset[str] = frozenset()
    searchable: tuple[str, ...] = ()

    @classmethod
    def of(cls, identifiers: frozenset[str]) -> Self:
        specific = frozenset(item for item in identifiers if cls._is_specific(item))
        plain = {PlainText.of(item) for item in specific}
        return cls(specific, tuple(sorted(plain)))

    @staticmethod
    def _is_specific(text: str) -> bool:
        return len(text) >= SEARCHABLE_LENGTH


@dataclass(frozen=True, slots=True)
class ItemContext:
    item: GoldenItem
    question: str
    forbidden_values: tuple[str, ...] = ()
    foreign: ForeignIdentifiers = field(default_factory=ForeignIdentifiers)
