from api.application.dto.invoice_dto import InvoiceDto
from api.domain.ports import InvoiceRepository


class FinancialService:
    def __init__(self, invoices: InvoiceRepository) -> None:
        self._invoices = invoices

    async def list_invoices(self) -> list[InvoiceDto]:
        invoices = await self._invoices.list_all()
        return [InvoiceDto.from_entity(invoice) for invoice in invoices]

    async def list_debts(self) -> list[InvoiceDto]:
        invoices = await self._invoices.list_all()
        return [InvoiceDto.from_entity(invoice) for invoice in invoices if invoice.is_debt()]
