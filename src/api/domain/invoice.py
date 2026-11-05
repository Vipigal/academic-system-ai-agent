from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from api.domain.money import Money


class InvoiceStatus(Enum):
    PAID = "paid"
    OPEN = "open"
    OVERDUE = "overdue"
    PARTIAL = "partial"
    RENEGOTIATED = "renegotiated"
    CANCELLED = "cancelled"


class InvoiceKind(Enum):
    TUITION = "tuition"
    AGREEMENT_INSTALLMENT = "agreement_installment"
    SERVICE_FEE = "service_fee"


class PaymentStatus(Enum):
    CONFIRMED = "confirmed"
    REVERSED = "reversed"


DEBT_STATUSES = frozenset({InvoiceStatus.OVERDUE, InvoiceStatus.PARTIAL})
SETTLED_STATUSES = frozenset({InvoiceStatus.CANCELLED, InvoiceStatus.RENEGOTIATED})
UPCOMING_STATUSES = frozenset({InvoiceStatus.OPEN, InvoiceStatus.PARTIAL})


@dataclass(frozen=True, slots=True)
class Payment:
    id: str
    invoice_id: str
    paid_at: datetime
    principal: Money
    late_charge: Money
    method: str
    status: PaymentStatus

    @property
    def amount(self) -> Money:
        return self.principal + self.late_charge

    @property
    def is_confirmed(self) -> bool:
        return self.status is PaymentStatus.CONFIRMED


@dataclass(frozen=True, slots=True)
class Invoice:
    id: str
    contract_id: str
    agreement_id: str | None
    kind: InvoiceKind
    competence: str
    due_date: date
    gross: Money
    net: Money
    status: InvoiceStatus
    payments: tuple[Payment, ...]
    late_charge: Money

    @property
    def paid(self) -> Money:
        return Money.total(payment.principal for payment in self.payments if payment.is_confirmed)

    @property
    def balance(self) -> Money:
        if self.status in SETTLED_STATUSES:
            return Money.from_cents(0)
        return self.net - self.paid

    def is_debt(self, reference: date) -> bool:
        return self.status in DEBT_STATUSES and self.due_date < reference

    def is_upcoming(self, reference: date) -> bool:
        return self.status in UPCOMING_STATUSES and self.due_date > reference

    def late_charge_due(self, reference: date) -> Money:
        return self.late_charge if self.is_debt(reference) else Money.from_cents(0)

    def amount_due(self, reference: date) -> Money:
        return self.balance + self.late_charge_due(reference)

    def days_overdue(self, reference: date) -> int:
        return (reference - self.due_date).days if self.is_debt(reference) else 0
