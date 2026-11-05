from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.application.dto.finance_payment import PaymentDto
from api.domain.invoice import Invoice, InvoiceKind, InvoiceStatus


class InvoiceDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    contract_id: str
    kind: InvoiceKind
    competence: str
    due_date: date
    net_amount_reais: Decimal
    balance_amount_reais: Decimal
    late_charge_reais: Decimal
    amount_due_reais: Decimal
    status: InvoiceStatus
    is_debt: bool
    payments: tuple[PaymentDto, ...]

    @classmethod
    def from_entity(cls, invoice: Invoice, reference: date) -> Self:
        return cls(
            id=invoice.id,
            contract_id=invoice.contract_id,
            kind=invoice.kind,
            competence=invoice.competence,
            due_date=invoice.due_date,
            net_amount_reais=invoice.net.reais,
            balance_amount_reais=invoice.balance.reais,
            late_charge_reais=invoice.late_charge_due(reference).reais,
            amount_due_reais=invoice.amount_due(reference).reais,
            status=invoice.status,
            is_debt=invoice.is_debt(reference),
            payments=tuple(PaymentDto.from_entity(payment) for payment in invoice.payments),
        )
