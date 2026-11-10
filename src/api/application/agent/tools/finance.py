from typing import Annotated

from api.application.agent.tool_arguments import FIRST_PAGE_ARGUMENT, PageArgument
from api.application.agent.tools.ui import ToolUi
from api.application.finance.dto import agreement, payment, tuition
from api.application.finance.dto.invoice import InvoiceDto
from api.application.finance.dto.summary import ContractSummaryDto
from api.application.finance.service import FinancialService
from api.application.shared.tool_parameters import FlagArgument, PeriodArgument, Teaching
from api.application.shared.tool_result import ToolResult
from api.domain.finance.invoice import InvoiceKind, InvoiceStatus

SUMMARY_UI = "Painel da situação financeira exibido ao aluno."


class FinanceTools:
    def __init__(self, service: FinancialService) -> None:
        self._service = service

    async def get_financial_summary(
        self, *, show_ui: FlagArgument = False
    ) -> ToolResult[list[ContractSummaryDto]]:
        """Resume os contratos do aluno. Use para saber dívida, próximo boleto, bolsas e pagador.

        Pode mostrar UI ao aluno com show_ui.
        """
        summary = await self._service.get_financial_summary()
        return ToolUi.shown(summary, SUMMARY_UI) if show_ui else summary

    async def list_invoices(
        self,
        status: InvoiceStatus | None = None,
        kind: InvoiceKind | None = None,
        period: PeriodArgument | None = None,
        page: PageArgument = FIRST_PAGE_ARGUMENT,
    ) -> ToolResult[list[InvoiceDto]]:
        """Lista faturas com pagamentos e saldo. Use para explicar uma fatura. period: AAAA-MM."""
        return await self._service.list_invoices(status, kind, period, page)

    async def list_payments(
        self,
        year: Annotated[int | None, Teaching("o ano com quatro dígitos, inteiro", "2026")] = None,
        page: PageArgument = FIRST_PAGE_ARGUMENT,
    ) -> ToolResult[list[payment.PaymentDto]]:
        """Lista os pagamentos confirmados do aluno. Use para saber o que já foi pago."""
        return await self._service.list_payments(year, page)

    async def get_tuition_changes(self) -> ToolResult[list[tuition.TuitionChangeDto]]:
        """Lista as mudanças de valor da mensalidade. Use para explicar por que ela mudou."""
        return await self._service.get_tuition_changes()

    async def list_agreements(self) -> ToolResult[list[agreement.AgreementDto]]:
        """Lista os acordos de renegociação do aluno. Use para saber quantas parcelas faltam."""
        return await self._service.list_agreements()
