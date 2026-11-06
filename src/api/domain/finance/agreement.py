from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from api.domain.finance.invoice import Invoice, InvoiceStatus
from api.domain.shared.money import Money


class AgreementStatus(Enum):
    ACTIVE = "active"
    SETTLED = "settled"
    BROKEN = "broken"


@dataclass(frozen=True, slots=True)
class Agreement:
    id: str
    contract_id: str
    status: AgreementStatus
    created_at: datetime
    original_debt: Money
    waived: Money
    agreed: Money
    installments: tuple[Invoice, ...]

    @property
    def paid_installments(self) -> tuple[Invoice, ...]:
        return tuple(item for item in self.installments if item.status is InvoiceStatus.PAID)

    @property
    def remaining_installments(self) -> tuple[Invoice, ...]:
        return tuple(item for item in self.installments if item.status is not InvoiceStatus.PAID)

    @property
    def remaining(self) -> Money:
        return Money.total(item.balance for item in self.remaining_installments)
