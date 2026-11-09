from collections.abc import Mapping, Sequence

from sqlalchemy import select

from api.domain.finance.agreement import Agreement
from api.domain.finance.contract import Contract
from api.domain.finance.invoice import Invoice
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.finance.charge_models import (
    AgreementRow,
    DiscountRow,
    LateChargeRow,
)
from api.persistence.finance.contract_mappers import AgreementMapper, ContractMapper
from api.persistence.finance.mappers import InvoiceMapper
from api.persistence.finance.models import InvoiceRow, PaymentRow
from api.persistence.identity.payer_queries import PayerQueries

SERVICE_FEE_KIND = "SERVICE_FEE"


class SqlFinanceRepository:
    def __init__(self, adapter: RepositoryAdapter) -> None:
        self._adapter = adapter

    async def list_invoices(self) -> Sequence[Invoice]:
        rows = await self._adapter.fetch(
            select(InvoiceRow).order_by(InvoiceRow.due_date, InvoiceRow.id)
        )
        payments = await self._adapter.fetch(
            select(PaymentRow).order_by(PaymentRow.paid_at, PaymentRow.id)
        )
        late_charges = await self._adapter.fetch(
            select(LateChargeRow).order_by(LateChargeRow.reference_date, LateChargeRow.id)
        )
        return InvoiceMapper.to_entities(rows, payments, late_charges)

    async def list_contracts(self) -> Sequence[Contract]:
        cpf = self._adapter.student_session.cpf
        rows = await self._adapter.fetch_rows(PayerQueries.contracts_with_payer(cpf))
        discounts = await self._adapter.fetch(
            select(DiscountRow).order_by(DiscountRow.valid_from, DiscountRow.id)
        )
        return ContractMapper.to_entities(rows, discounts)

    async def list_agreements(self) -> Sequence[Agreement]:
        rows = await self._adapter.fetch(
            select(AgreementRow).order_by(AgreementRow.created_at, AgreementRow.id)
        )
        return AgreementMapper.to_entities(rows, await self.list_invoices())

    async def list_service_fees(self) -> Mapping[str, Invoice]:
        rows = await self._adapter.fetch(
            select(InvoiceRow).where(InvoiceRow.kind == SERVICE_FEE_KIND)
        )
        by_id = {invoice.id: invoice for invoice in await self.list_invoices()}
        return {row.protocol_ref: by_id[row.id] for row in rows if row.protocol_ref}
