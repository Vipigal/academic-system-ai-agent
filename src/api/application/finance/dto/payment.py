from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.domain.finance.invoice import Payment, PaymentStatus


class PaymentDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    invoice_id: str
    paid_at: datetime
    amount_reais: Decimal
    principal_reais: Decimal
    late_charge_reais: Decimal
    method: str
    status: PaymentStatus

    @classmethod
    def from_entity(cls, payment: Payment) -> Self:
        return cls(
            id=payment.id,
            invoice_id=payment.invoice_id,
            paid_at=payment.paid_at,
            amount_reais=payment.amount.reais,
            principal_reais=payment.principal.reais,
            late_charge_reais=payment.late_charge.reais,
            method=payment.method,
            status=payment.status,
        )
