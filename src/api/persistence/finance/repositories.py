from collections.abc import Sequence

from sqlalchemy import select

from api.domain.finance_agreement import Agreement
from api.domain.finance_contract import Contract
from api.domain.invoice import Invoice
from api.persistence.finance.charge_models import (
    AgreementRow,
    DiscountRow,
    LateChargeRow,
)
from api.persistence.finance.contract_mappers import AgreementMapper, ContractMapper
from api.persistence.finance.mappers import InvoiceMapper
from api.persistence.finance.models import ContractRow, InvoiceRow, PaymentRow
from api.persistence.repository_adapter import RepositoryAdapter


class SqlFinanceRepository:
    def __init__(self, adapter: RepositoryAdapter) -> None:
        self._adapter = adapter

    async def list_invoices(self) -> Sequence[Invoice]:
        rows = await self._adapter.fetch(
            select(InvoiceRow).order_by(InvoiceRow.due_date, InvoiceRow.id)
        )
        payments = await self._adapter.fetch(
            select(PaymentRow)
            .join(InvoiceRow, PaymentRow.invoice_id == InvoiceRow.id)
            .order_by(PaymentRow.paid_at, PaymentRow.id)
        )
        late_charges = await self._adapter.fetch(
            select(LateChargeRow)
            .join(InvoiceRow, LateChargeRow.invoice_id == InvoiceRow.id)
            .order_by(LateChargeRow.reference_date, LateChargeRow.id)
        )
        return InvoiceMapper.to_entities(rows, payments, late_charges)

    async def list_contracts(self) -> Sequence[Contract]:
        rows = await self._adapter.fetch(select(ContractRow).order_by(ContractRow.id))
        discounts = await self._adapter.fetch(
            select(DiscountRow).order_by(DiscountRow.valid_from, DiscountRow.id)
        )
        session = self._adapter.student_session
        return ContractMapper.to_entities(
            rows, discounts, session.self_paid_contract_ids, session.company_paid_contract_ids
        )

    async def list_agreements(self) -> Sequence[Agreement]:
        rows = await self._adapter.fetch(
            select(AgreementRow).order_by(AgreementRow.created_at, AgreementRow.id)
        )
        return AgreementMapper.to_entities(rows, await self.list_invoices())
