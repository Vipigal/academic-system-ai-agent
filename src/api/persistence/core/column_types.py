from datetime import UTC, date, datetime
from decimal import Decimal
from typing import override
from zoneinfo import ZoneInfo

from sqlalchemy import Dialect, String, TypeDecorator

from api.domain.shared.money import Money

BRASILIA = ZoneInfo("America/Sao_Paulo")
SOURCE_MOMENT = "%Y-%m-%dT%H:%M:%SZ"


class UnknownDialectValueError(ValueError):
    def __init__(self, vocabulary: str, value: str) -> None:
        super().__init__(f"valor fora do vocabulário {vocabulary}: {value!r}")
        self.vocabulary = vocabulary
        self.value = value


class SourceText[ValueT](TypeDecorator[ValueT]):
    impl = String
    cache_ok = True

    @override
    def process_bind_param(self, value: ValueT | None, dialect: Dialect) -> str | None:
        return None if value is None else self.to_source(value)

    @override
    def process_result_value(self, value: str | None, dialect: Dialect) -> ValueT | None:
        return None if value is None else self.from_source(value)

    def to_source(self, value: ValueT) -> str:
        raise NotImplementedError

    def from_source(self, text: str) -> ValueT:
        raise NotImplementedError


class TextFlag(SourceText[bool]):
    cache_ok = True

    def __init__(self, true_text: str, false_text: str) -> None:
        super().__init__()
        self.true_text = true_text
        self.false_text = false_text

    @override
    def to_source(self, value: bool) -> str:
        return self.true_text if value else self.false_text

    @override
    def from_source(self, text: str) -> bool:
        if text == self.true_text:
            return True
        if text == self.false_text:
            return False
        raise UnknownDialectValueError(f"TextFlag({self.true_text}/{self.false_text})", text)


TRUE_FALSE = TextFlag("True", "False")


class TextCents(SourceText[Money]):
    cache_ok = True

    @override
    def to_source(self, value: Money) -> str:
        return str(value.cents)

    @override
    def from_source(self, text: str) -> Money:
        return Money(int(text))


class TextDecimal(SourceText[Decimal]):
    cache_ok = True

    @override
    def to_source(self, value: Decimal) -> str:
        return str(value)

    @override
    def from_source(self, text: str) -> Decimal:
        return Decimal(text)


class IsoDate(SourceText[date]):
    cache_ok = True

    @override
    def to_source(self, value: date) -> str:
        return value.isoformat()

    @override
    def from_source(self, text: str) -> date:
        return date.fromisoformat(text)


class UtcMoment(SourceText[datetime]):
    cache_ok = True

    @override
    def to_source(self, value: datetime) -> str:
        return value.astimezone(UTC).strftime(SOURCE_MOMENT)

    @override
    def from_source(self, text: str) -> datetime:
        return datetime.fromisoformat(text).astimezone(BRASILIA)
