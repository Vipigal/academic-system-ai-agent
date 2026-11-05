from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.domain.finance_agreement import Agreement, AgreementStatus
from api.domain.invoice import Invoice, InvoiceStatus


class InstallmentDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    invoice_id: str
    due_date: date
    amount_reais: Decimal
    status: InvoiceStatus

    @classmethod
    def from_entity(cls, invoice: Invoice) -> Self:
        return cls(
            invoice_id=invoice.id,
            due_date=invoice.due_date,
            amount_reais=invoice.balance.reais,
            status=invoice.status,
        )


class AgreementDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    contract_id: str
    status: AgreementStatus
    created_on: date
    original_debt_reais: Decimal
    waived_reais: Decimal
    agreed_reais: Decimal
    installments_total: int
    installments_paid: int
    installments_remaining: int
    remaining_reais: Decimal
    remaining_installments: tuple[InstallmentDto, ...]

    @classmethod
    def from_entity(cls, agreement: Agreement) -> Self:
        return cls(
            id=agreement.id,
            contract_id=agreement.contract_id,
            status=agreement.status,
            created_on=agreement.created_at.date(),
            original_debt_reais=agreement.original_debt.reais,
            waived_reais=agreement.waived.reais,
            agreed_reais=agreement.agreed.reais,
            installments_total=len(agreement.installments),
            installments_paid=len(agreement.paid_installments),
            installments_remaining=len(agreement.remaining_installments),
            remaining_reais=agreement.remaining.reais,
            remaining_installments=tuple(
                InstallmentDto.from_entity(invoice) for invoice in agreement.remaining_installments
            ),
        )
