from api.application.agent.tools.registry import ToolRegistry
from api.application.overview.dto.pending import PendingItemsDto
from api.application.overview.service import OverviewService
from api.application.shared.tool_result import ToolResult
from api.domain.ontology import (
    academic_enrollment,
    academic_performance,
    finance_charges,
    lms,
    overview,
    protocols,
)


class OverviewTools:
    def __init__(self, service: OverviewService) -> None:
        self._service = service

    @ToolRegistry.declares(
        overview.PENDENCIA,
        academic_enrollment.MATRICULA,
        finance_charges.DIVIDA,
        academic_performance.FREQUENCIA,
        protocols.PROTOCOLO,
        lms.PROVA_ONLINE,
    )
    async def get_pending_items(self) -> ToolResult[PendingItemsDto]:
        """Verifica matrícula, dívida, vencimentos de 30 dias, protocolos, frequência e provas.

        Use para "está tudo em dia?"; devolve o que foi verificado e o que merece atenção.
        """
        return await self._service.get_pending_items()
