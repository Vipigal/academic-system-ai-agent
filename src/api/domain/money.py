from dataclasses import dataclass
from decimal import Decimal
from typing import Self

CENTS_EXPONENT = -2


@dataclass(frozen=True, slots=True)
class Money:
    cents: int

    @classmethod
    def from_cents(cls, cents: int) -> Self:
        return cls(cents)

    @property
    def reais(self) -> Decimal:
        return Decimal(self.cents).scaleb(CENTS_EXPONENT)
