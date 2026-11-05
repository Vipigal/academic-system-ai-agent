from api.application.dto.finance_agreement import AgreementDto
from api.application.dto.finance_payment import PaymentDto
from api.application.dto.finance_summary import ContractSummaryDto
from api.application.dto.finance_tuition import TuitionChangeDto
from api.application.dto.invoice_dto import InvoiceDto
from api.application.dto.tool_result import ToolResult
from api.application.financial_service import FinancialService
from api.application.page import FIRST_PAGE, PageRequest
from api.domain.invoice import InvoiceKind, InvoiceStatus
from api.domain.ontology.finance_charges import (
    ACORDO,
    BOLSA,
    DIVIDA,
    MENSALIDADE,
    MULTA_E_JUROS,
    PARCELA_DE_ACORDO,
    PROXIMO_BOLETO,
)
from api.domain.ontology.finance_settlement import COBRANCA, ESTORNO, PAGADOR, PAGAMENTO, QUITACAO
from api.presentation.tools.registry import ToolRegistry


class FinanceTools:
    def __init__(self, service: FinancialService) -> None:
        self._service = service

    @ToolRegistry.declares(DIVIDA, MULTA_E_JUROS, PROXIMO_BOLETO, BOLSA, PAGADOR, COBRANCA)
    async def get_financial_summary(self) -> ToolResult[list[ContractSummaryDto]]:
        """Resume os contratos do aluno. Use para saber dívida, próximo boleto, bolsas e pagador."""
        return await self._service.get_financial_summary()

    @ToolRegistry.declares(MENSALIDADE, PARCELA_DE_ACORDO, ESTORNO, PAGAMENTO, QUITACAO)
    async def list_invoices(
        self,
        status: InvoiceStatus | None = None,
        kind: InvoiceKind | None = None,
        period: str | None = None,
        page: PageRequest = FIRST_PAGE,
    ) -> ToolResult[list[InvoiceDto]]:
        """Lista faturas com pagamentos e saldo. Use para explicar uma fatura. period: AAAA-MM."""
        return await self._service.list_invoices(status, kind, period, page)

    @ToolRegistry.declares(PAGAMENTO, ESTORNO)
    async def list_payments(
        self, year: int | None = None, page: PageRequest = FIRST_PAGE
    ) -> ToolResult[list[PaymentDto]]:
        """Lista os pagamentos confirmados do aluno. Use para saber o que já foi pago."""
        return await self._service.list_payments(year, page)

    @ToolRegistry.declares(MENSALIDADE, BOLSA)
    async def get_tuition_changes(self) -> ToolResult[list[TuitionChangeDto]]:
        """Lista as mudanças de valor da mensalidade. Use para explicar por que ela mudou."""
        return await self._service.get_tuition_changes()

    @ToolRegistry.declares(ACORDO, PARCELA_DE_ACORDO)
    async def list_agreements(self) -> ToolResult[list[AgreementDto]]:
        """Lista os acordos de renegociação do aluno. Use para saber quantas parcelas faltam."""
        return await self._service.list_agreements()
