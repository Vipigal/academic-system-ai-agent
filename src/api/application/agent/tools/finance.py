from api.application.agent.tools.registry import ToolRegistry
from api.application.agent.tools.ui import shown
from api.application.finance.dto.agreement import AgreementDto
from api.application.finance.dto.invoice import InvoiceDto
from api.application.finance.dto.payment import PaymentDto
from api.application.finance.dto.summary import ContractSummaryDto
from api.application.finance.dto.tuition import TuitionChangeDto
from api.application.finance.service import FinancialService
from api.application.shared.page import FIRST_PAGE, PageRequest
from api.application.shared.tool_result import ToolResult
from api.domain.finance.invoice import InvoiceKind, InvoiceStatus
from api.domain.ontology import finance_charges, finance_settlement

SUMMARY_UI = "Painel da situação financeira exibido ao aluno."


class FinanceTools:
    def __init__(self, service: FinancialService) -> None:
        self._service = service

    @ToolRegistry.declares(
        finance_charges.DIVIDA,
        finance_charges.MULTA_E_JUROS,
        finance_charges.PROXIMO_BOLETO,
        finance_charges.BOLSA,
        finance_settlement.PAGADOR,
        finance_settlement.COBRANCA,
    )
    async def get_financial_summary(
        self, *, show_ui: bool = False
    ) -> ToolResult[list[ContractSummaryDto]]:
        """Resume os contratos do aluno. Use para saber dívida, próximo boleto, bolsas e pagador.

        Pode mostrar UI ao aluno com show_ui.
        """
        summary = await self._service.get_financial_summary()
        return shown(summary, SUMMARY_UI) if show_ui else summary

    @ToolRegistry.declares(
        finance_charges.MENSALIDADE,
        finance_charges.PARCELA_DE_ACORDO,
        finance_settlement.ESTORNO,
        finance_settlement.PAGAMENTO,
        finance_settlement.QUITACAO,
    )
    async def list_invoices(
        self,
        status: InvoiceStatus | None = None,
        kind: InvoiceKind | None = None,
        period: str | None = None,
        page: PageRequest = FIRST_PAGE,
    ) -> ToolResult[list[InvoiceDto]]:
        """Lista faturas com pagamentos e saldo. Use para explicar uma fatura. period: AAAA-MM."""
        return await self._service.list_invoices(status, kind, period, page)

    @ToolRegistry.declares(finance_settlement.PAGAMENTO, finance_settlement.ESTORNO)
    async def list_payments(
        self, year: int | None = None, page: PageRequest = FIRST_PAGE
    ) -> ToolResult[list[PaymentDto]]:
        """Lista os pagamentos confirmados do aluno. Use para saber o que já foi pago."""
        return await self._service.list_payments(year, page)

    @ToolRegistry.declares(finance_charges.MENSALIDADE, finance_charges.BOLSA)
    async def get_tuition_changes(self) -> ToolResult[list[TuitionChangeDto]]:
        """Lista as mudanças de valor da mensalidade. Use para explicar por que ela mudou."""
        return await self._service.get_tuition_changes()

    @ToolRegistry.declares(finance_charges.ACORDO, finance_charges.PARCELA_DE_ACORDO)
    async def list_agreements(self) -> ToolResult[list[AgreementDto]]:
        """Lista os acordos de renegociação do aluno. Use para saber quantas parcelas faltam."""
        return await self._service.list_agreements()
