from api.application.dto.invoice_dto import InvoiceDto
from api.domain.ports.clock import Clock
from api.domain.ports.finance import InvoiceRepository


class FinancialService:
    def __init__(self, invoices: InvoiceRepository, clock: Clock) -> None:
        self._invoices = invoices
        self._clock = clock

    async def list_invoices(self) -> list[InvoiceDto]:
        invoices = await self._invoices.list_all()
        reference = self._clock.today()
        return [InvoiceDto.from_entity(invoice, reference) for invoice in invoices]

    async def list_debts(self) -> list[InvoiceDto]:
        reference = self._clock.today()
        invoices = await self._invoices.list_all()
        return [
            InvoiceDto.from_entity(invoice, reference)
            for invoice in invoices
            if invoice.is_debt(reference)
        ]
