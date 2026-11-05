from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.domain.invoice import Invoice, InvoiceStatus


class InvoiceDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    due_date: date
    net_amount_reais: Decimal
    status: InvoiceStatus
    is_debt: bool

    @classmethod
    def from_entity(cls, invoice: Invoice) -> Self:
        return cls(
            id=invoice.id,
            due_date=invoice.due_date,
            net_amount_reais=invoice.net.reais,
            status=invoice.status,
            is_debt=invoice.is_debt(),
        )
