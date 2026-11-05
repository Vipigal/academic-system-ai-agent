from api.application.dto.overview_pending_dto import PendingItemsDto
from api.application.dto.tool_result import ToolResult
from api.application.overview_service import OverviewService
from api.domain.ontology import (
    academic_enrollment,
    academic_performance,
    finance_charges,
    lms,
    overview,
    protocols,
)
from api.presentation.tools.registry import ToolRegistry


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
