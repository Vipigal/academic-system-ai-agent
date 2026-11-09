from collections.abc import Mapping
from enum import Enum
from typing import Self, override

from api.persistence.core.column_types import SourceText


class UnknownDialectValueError(ValueError):
    pass


class SourceEnum[MemberT: Enum](SourceText[MemberT]):
    cache_ok = True

    def __init__(self, vocabulary: Mapping[str, MemberT]) -> None:
        super().__init__()
        self.vocabulary = tuple(vocabulary.items())
        self._members = dict(vocabulary)
        self._sources = {member: source for source, member in reversed(self.vocabulary)}

    @classmethod
    def by_name(cls, members: type[MemberT]) -> Self:
        return cls({member.name: member for member in members})

    @classmethod
    def by_value(cls, members: type[MemberT]) -> Self:
        return cls({member.value: member for member in members})

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(self._members)

    def member_of(self, source: str) -> MemberT:
        if source not in self._members:
            raise UnknownDialectValueError(source)
        return self._members[source]

    @override
    def to_source(self, value: MemberT) -> str:
        return self._sources[value]

    @override
    def from_source(self, text: str) -> MemberT:
        return self.member_of(text)
