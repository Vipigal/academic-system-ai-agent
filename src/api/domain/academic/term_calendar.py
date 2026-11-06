import re
from dataclasses import dataclass
from datetime import date

TERM_CODE = re.compile(r"\d{4}/\d")


@dataclass(frozen=True, slots=True)
class Term:
    code: str
    start_date: date
    end_date: date
    av1_start: date
    av2_start: date
    is_current: bool


@dataclass(frozen=True, slots=True)
class AcademicCalendar:
    terms: tuple[Term, ...]

    @property
    def first(self) -> Term:
        return self.terms[0]

    @property
    def last(self) -> Term:
        return self.terms[-1]

    @property
    def current(self) -> Term:
        return next((term for term in self.terms if term.is_current), self.last)

    def find(self, code: str) -> Term | None:
        return next((term for term in self.terms if term.code == code), None)

    def is_after_last(self, code: str) -> bool:
        return TERM_CODE.fullmatch(code) is not None and code > self.last.code
