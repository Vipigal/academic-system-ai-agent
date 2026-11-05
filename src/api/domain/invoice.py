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
    paid: Money

    @property
    def balance(self) -> Money:
        return self.net - self.paid

    def is_debt(self, reference: date) -> bool:
        return self.status in DEBT_STATUSES and self.due_date < reference
