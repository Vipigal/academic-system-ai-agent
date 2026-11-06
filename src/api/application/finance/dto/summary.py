from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.domain.finance.contract import Contract, ContractSituation, PayerType, Scholarship
from api.domain.finance.debt import DebtPosition
from api.domain.finance.invoice import Invoice, InvoiceKind


class DebtItemDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    invoice_id: str
    kind: InvoiceKind
    competence: str
    due_date: date
    principal_reais: Decimal
    late_charge_reais: Decimal

    @classmethod
    def from_entity(cls, invoice: Invoice, reference: date) -> Self:
        return cls(
            invoice_id=invoice.id,
            kind=invoice.kind,
            competence=invoice.competence,
            due_date=invoice.due_date,
            principal_reais=invoice.balance.reais,
            late_charge_reais=invoice.late_charge_due(reference).reais,
        )


class DebtDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    reference_date: date
    principal_reais: Decimal
    late_charge_reais: Decimal
    total_reais: Decimal
    overdue_invoices: int
    max_days_overdue: int
    items: tuple[DebtItemDto, ...]

    @classmethod
    def from_position(cls, position: DebtPosition) -> Self:
        return cls(
            reference_date=position.reference,
            principal_reais=position.principal.reais,
            late_charge_reais=position.late_charge.reais,
            total_reais=position.total.reais,
            overdue_invoices=len(position.invoices),
            max_days_overdue=position.max_days_overdue,
            items=tuple(
                DebtItemDto.from_entity(invoice, position.reference)
                for invoice in position.invoices
            ),
        )


class NextInvoiceDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    invoice_id: str
    kind: InvoiceKind
    due_date: date
    amount_reais: Decimal

    @classmethod
    def from_entity(cls, invoice: Invoice) -> Self:
        return cls(
            invoice_id=invoice.id,
            kind=invoice.kind,
            due_date=invoice.due_date,
            amount_reais=invoice.balance.reais,
        )


class ScholarshipDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: str
    rate: Decimal
    valid_from: date
    valid_to: date | None
    is_active: bool

    @classmethod
    def from_entity(cls, scholarship: Scholarship, reference: date) -> Self:
        return cls(
            kind=scholarship.kind,
            rate=scholarship.rate,
            valid_from=scholarship.valid_from,
            valid_to=scholarship.valid_to,
            is_active=scholarship.is_active_on(reference),
        )


class ContractSummaryDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract_id: str
    course_code: str
    situation: ContractSituation
    payer: PayerType
    debt: DebtDto
    next_invoice: NextInvoiceDto | None
    scholarships: tuple[ScholarshipDto, ...]
    tuition_invoices: int

    @classmethod
    def from_entity(cls, contract: Contract, invoices: Iterable[Invoice], reference: date) -> Self:
        own = [invoice for invoice in invoices if invoice.contract_id == contract.id]
        return cls(
            contract_id=contract.id,
            course_code=contract.course_code,
            situation=contract.situation,
            payer=contract.payer,
            debt=DebtDto.from_position(DebtPosition.of(own, reference)),
            next_invoice=cls._next_invoice(own, reference),
            scholarships=tuple(
                ScholarshipDto.from_entity(scholarship, reference)
                for scholarship in contract.scholarships
            ),
            tuition_invoices=sum(invoice.kind is InvoiceKind.TUITION for invoice in own),
        )

    @staticmethod
    def _next_invoice(invoices: Iterable[Invoice], reference: date) -> NextInvoiceDto | None:
        upcoming = [invoice for invoice in invoices if invoice.is_upcoming(reference)]
        if not upcoming:
            return None
        first = min(upcoming, key=lambda invoice: (invoice.due_date, invoice.id))
        return NextInvoiceDto.from_entity(first)
