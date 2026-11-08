import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from api.application.shared.tool_result import Candidate

COMBINING_MARK = "Mn"
NO_ALIASES: Mapping[str, str] = {}


@dataclass(frozen=True, slots=True)
class NameMatch:
    query: str | None
    candidates: tuple[Candidate, ...]
    matched: tuple[Candidate, ...]

    @property
    def missed(self) -> bool:
        return self.query is not None and not self.matched

    @property
    def is_ambiguous(self) -> bool:
        return len(self.matched) > 1

    @property
    def codes(self) -> frozenset[str]:
        return frozenset(candidate.code for candidate in self.matched)


@dataclass(frozen=True, slots=True)
class Searchable:
    candidate: Candidate
    texts: tuple[str, ...]

    def equals(self, needle: str) -> bool:
        return needle in self.texts

    def contains(self, needle: str) -> bool:
        return any(needle in text for text in self.texts)


class NameSearch:
    @classmethod
    def search(
        cls,
        query: str | None,
        candidates: Iterable[Candidate],
        aliases: Mapping[str, str] = NO_ALIASES,
    ) -> NameMatch:
        unique = tuple(sorted(set(candidates), key=lambda candidate: candidate.code))
        if query is None:
            return NameMatch(query, unique, unique)
        searchable = tuple(cls._searchable(item, aliases) for item in unique)
        return NameMatch(query, unique, cls._matching(cls._normalized(query), searchable))

    @staticmethod
    def _matching(needle: str, searchable: tuple[Searchable, ...]) -> tuple[Candidate, ...]:
        if not needle:
            return ()
        exact = tuple(item.candidate for item in searchable if item.equals(needle))
        partial = tuple(item.candidate for item in searchable if item.contains(needle))
        return exact or partial

    @classmethod
    def _searchable(cls, candidate: Candidate, aliases: Mapping[str, str]) -> Searchable:
        texts = (candidate.code, candidate.name, aliases.get(candidate.code, ""))
        return Searchable(candidate, tuple(cls._normalized(text) for text in texts if text))

    @staticmethod
    def _normalized(text: str) -> str:
        decomposed = unicodedata.normalize("NFKD", text)
        kept = (char for char in decomposed if unicodedata.category(char) != COMBINING_MARK)
        return " ".join("".join(kept).casefold().split())
