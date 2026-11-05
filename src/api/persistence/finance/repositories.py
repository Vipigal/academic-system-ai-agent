from collections.abc import Sequence

from sqlalchemy import select

from api.domain.invoice import Invoice
from api.persistence.finance.dialect import FinanceDialect
from api.persistence.finance.mappers import InvoiceMapper
from api.persistence.finance.models import InvoiceRow, PaymentRow
from api.persistence.repository_adapter import RepositoryAdapter


class FinanceInvoiceRepository:
    def __init__(self, adapter: RepositoryAdapter) -> None:
        self._adapter = adapter

    async def list_all(self) -> Sequence[Invoice]:
        rows = await self._adapter.fetch(select(InvoiceRow).order_by(InvoiceRow.due_date))
        payments = await self._adapter.fetch(
            select(PaymentRow)
            .join(InvoiceRow, PaymentRow.invoice_id == InvoiceRow.id)
            .where(FinanceDialect.confirmed_payment())
        )
        return InvoiceMapper.to_entities(rows, payments)
