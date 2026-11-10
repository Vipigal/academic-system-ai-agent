from collections.abc import Mapping
from enum import Enum
from typing import Self, override

from api.persistence.core.column_types import SourceText, UnknownDialectValueError


class SourceEnum[MemberT: Enum](SourceText[MemberT]):
    cache_ok = True

    def __init__(self, vocabulary: Mapping[str, MemberT]) -> None:
        super().__init__()
        self.vocabulary = tuple(vocabulary.items())
        self._members = dict(vocabulary)
        self._sources = {member: source for source, member in reversed(self.vocabulary)}
        self._name = type(next(iter(self._members.values()))).__name__

    @classmethod
    def by_name(cls, members: type[MemberT]) -> Self:
        return cls({member.name: member for member in members})

    @classmethod
    def by_value(cls, members: type[MemberT]) -> Self:
        return cls({member.value: member for member in members})

    @classmethod
    def inverse_of(cls, sources: Mapping[MemberT, str]) -> Self:
        return cls({source: member for member, source in sources.items()})

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(self._members)

    @override
    def to_source(self, value: MemberT) -> str:
        return self._sources[value]

    @override
    def from_source(self, text: str) -> MemberT:
        if text not in self._members:
            raise UnknownDialectValueError(self._name, text)
        return self._members[text]
