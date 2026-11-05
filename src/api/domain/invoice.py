from dataclasses import dataclass
from datetime import date
from enum import Enum

from api.domain.money import Money


class InvoiceStatus(Enum):
    PAID = "paid"
    OPEN = "open"
    OVERDUE = "overdue"
    PARTIAL = "partial"
    RENEGOTIATED = "renegotiated"
    CANCELLED = "cancelled"


DEBT_STATUSES = frozenset({InvoiceStatus.OVERDUE, InvoiceStatus.PARTIAL})


@dataclass(frozen=True, slots=True)
class Invoice:
    id: str
    due_date: date
    net: Money
    status: InvoiceStatus

    def is_debt(self) -> bool:
        return self.status in DEBT_STATUSES
