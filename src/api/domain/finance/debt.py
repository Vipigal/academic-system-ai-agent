from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from typing import Self

from api.domain.finance.invoice import Invoice
from api.domain.shared.money import Money


@dataclass(frozen=True, slots=True)
class DebtPosition:
    reference: date
    invoices: tuple[Invoice, ...]

    @classmethod
    def of(cls, invoices: Iterable[Invoice], reference: date) -> Self:
        return cls(reference, tuple(invoice for invoice in invoices if invoice.is_debt(reference)))

    @property
    def principal(self) -> Money:
        return Money.total(invoice.balance for invoice in self.invoices)

    @property
    def late_charge(self) -> Money:
        return Money.total(invoice.late_charge_due(self.reference) for invoice in self.invoices)

    @property
    def total(self) -> Money:
        return self.principal + self.late_charge

    @property
    def max_days_overdue(self) -> int:
        return max((invoice.days_overdue(self.reference) for invoice in self.invoices), default=0)
