from api.application.finance.dto.agreement import AgreementDto
from api.application.finance.dto.invoice import InvoiceDto
from api.application.finance.dto.payment import PaymentDto
from api.application.finance.dto.summary import ContractSummaryDto
from api.application.finance.dto.tuition import TuitionChangeDto
from api.application.finance.totals import FinanceTotals
from api.application.shared.page import FIRST_PAGE, PageRequest
from api.application.shared.period_filter import PeriodFilter
from api.application.shared.tool_result import ToolResult
from api.domain.finance.invoice import InvoiceKind, InvoiceStatus
from api.domain.ports.clock import Clock
from api.domain.ports.finance import FinanceRepository


class FinancialService:
    def __init__(self, finance: FinanceRepository, clock: Clock) -> None:
        self._finance = finance
        self._clock = clock

    async def get_financial_summary(self) -> ToolResult[list[ContractSummaryDto]]:
        reference = self._clock.today()
        contracts = await self._finance.list_contracts()
        invoices = await self._finance.list_invoices()
        summaries = [
            ContractSummaryDto.from_entity(contract, invoices, reference) for contract in contracts
        ]
        return ToolResult.items(summaries, totals=FinanceTotals.of_debt(invoices, reference))

    async def list_invoices(
        self,
        status: InvoiceStatus | None = None,
        kind: InvoiceKind | None = None,
        period: str | None = None,
        page: PageRequest = FIRST_PAGE,
    ) -> ToolResult[list[InvoiceDto]]:
        reference = self._clock.today()
        selected = [
            invoice
            for invoice in await self._finance.list_invoices()
            if status in {None, invoice.status}
            and kind in {None, invoice.kind}
            and PeriodFilter.matches(period, invoice.competence)
        ]
        dtos = [InvoiceDto.from_entity(invoice, reference) for invoice in selected]
        return ToolResult.listing(
            page.paginate(dtos), totals=FinanceTotals.of_invoices(selected, reference)
        )

    async def list_debts(self) -> ToolResult[list[InvoiceDto]]:
        reference = self._clock.today()
        invoices = await self._finance.list_invoices()
        dtos = [
            InvoiceDto.from_entity(invoice, reference)
            for invoice in invoices
            if invoice.is_debt(reference)
        ]
        return ToolResult.items(dtos, totals=FinanceTotals.of_debt(invoices, reference))

    async def list_payments(
        self, year: int | None = None, page: PageRequest = FIRST_PAGE
    ) -> ToolResult[list[PaymentDto]]:
        invoices = await self._finance.list_invoices()
        payments = sorted(
            (
                payment
                for invoice in invoices
                for payment in invoice.payments
                if year in {None, payment.paid_at.year}
            ),
            key=lambda payment: (payment.paid_at, payment.id),
        )
        confirmed = [
            PaymentDto.from_entity(payment) for payment in payments if payment.is_confirmed
        ]
        return ToolResult.listing(
            page.paginate(confirmed), totals=FinanceTotals.of_payments(payments)
        )

    async def get_tuition_changes(self) -> ToolResult[list[TuitionChangeDto]]:
        contracts = await self._finance.list_contracts()
        invoices = await self._finance.list_invoices()
        return ToolResult.items(TuitionChangeDto.history_of(contracts, invoices))

    async def list_agreements(self) -> ToolResult[list[AgreementDto]]:
        agreements = await self._finance.list_agreements()
        return ToolResult.items([AgreementDto.from_entity(agreement) for agreement in agreements])
