from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Self

CENTS_EXPONENT = -2


@dataclass(frozen=True, slots=True)
class Money:
    cents: int

    @classmethod
    def total(cls, values: Iterable[Money]) -> Self:
        return cls(sum(value.cents for value in values))

    def __add__(self, other: Self) -> Self:
        return type(self)(self.cents + other.cents)

    def __sub__(self, other: Self) -> Self:
        return type(self)(self.cents - other.cents)

    @property
    def reais(self) -> Decimal:
        return Decimal(self.cents).scaleb(CENTS_EXPONENT)
