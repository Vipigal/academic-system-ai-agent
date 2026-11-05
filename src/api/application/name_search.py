import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

from api.application.dto.tool_result import Candidate

COMBINING_MARK = "Mn"


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


class NameSearch:
    @classmethod
    def search(cls, query: str | None, candidates: Iterable[Candidate]) -> NameMatch:
        unique = tuple(sorted(set(candidates), key=lambda candidate: candidate.code))
        if query is None:
            return NameMatch(query, unique, unique)
        return NameMatch(query, unique, cls._matching(cls._normalized(query), unique))

    @classmethod
    def _matching(cls, needle: str, candidates: tuple[Candidate, ...]) -> tuple[Candidate, ...]:
        if not needle:
            return ()
        exact = tuple(item for item in candidates if needle in cls._searchable(item))
        partial = tuple(
            item for item in candidates if any(needle in text for text in cls._searchable(item))
        )
        return exact or partial

    @classmethod
    def _searchable(cls, candidate: Candidate) -> tuple[str, str]:
        return cls._normalized(candidate.code), cls._normalized(candidate.name)

    @staticmethod
    def _normalized(text: str) -> str:
        decomposed = unicodedata.normalize("NFKD", text)
        kept = (char for char in decomposed if unicodedata.category(char) != COMBINING_MARK)
        return " ".join("".join(kept).casefold().split())
