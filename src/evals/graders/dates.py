import re
from collections.abc import Iterator
from dataclasses import dataclass

from evals.graders.formats import ISO_DATE, FactValueError
from evals.graders.text import PlainText

MONTHS = (
    "janeiro",
    "fevereiro",
    "marco",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)
NUMERIC = re.compile(r"(?<![\d/])(\d{1,2})/(\d{1,2})(?:/(\d{4}|\d{2}))?(?![\d/])")
ISO = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
SPELLED = re.compile(r"(?<!\d)(\d{1,2})o? de (" + "|".join(MONTHS) + r")(?: de (\d{4}))?")
CENTURY = 2000
SHORT_YEAR = 2


@dataclass(frozen=True, slots=True)
class DateMention:
    day: int
    month: int
    year: int | None

    def matches(self, other: DateMention) -> bool:
        same_day = (self.day, self.month) == (other.day, other.month)
        return same_day and self._same_year(other.year)

    def _same_year(self, year: int | None) -> bool:
        if self.year is None or year is None:
            return True
        return self.year == year


class TextDates:
    @staticmethod
    def of_iso(value: str) -> DateMention:
        found = ISO_DATE.match(value)
        if found is None:
            raise FactValueError(f"data fora do formato ISO: {value}")
        year, month, day = found.groups()
        return DateMention(int(day), int(month), int(year))

    @classmethod
    def mentions(cls, text: str, iso_value: str) -> bool:
        wanted = cls.of_iso(iso_value)
        return any(wanted.matches(found) for found in cls.found_in(text))

    @classmethod
    def found_in(cls, text: str) -> Iterator[DateMention]:
        for day, month, year in NUMERIC.findall(text):
            yield DateMention(int(day), int(month), cls._year(year))
        for year, month, day in ISO.findall(text):
            yield DateMention(int(day), int(month), int(year))
        for day, month_name, year in SPELLED.findall(PlainText.of(text)):
            month = MONTHS.index(month_name) + 1
            yield DateMention(int(day), month, cls._year(year))

    @staticmethod
    def _year(digits: str) -> int | None:
        if not digits:
            return None
        year = int(digits)
        return year + CENTURY if len(digits) == SHORT_YEAR else year
