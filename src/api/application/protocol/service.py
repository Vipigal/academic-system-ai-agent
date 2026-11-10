from api.application.protocol.dto.catalog import ServiceOfferDto
from api.application.protocol.dto.detail import ProtocolDetailDto
from api.application.protocol.dto.proposal import Proposal
from api.application.protocol.dto.request import ProtocolDto
from api.application.protocol.proposer import ProtocolProposer
from api.application.protocol.queries import ProtocolQueries
from api.application.shared.page import PageRequest
from api.application.shared.tool_result import ToolResult
from api.domain.protocol.action import ProtocolAction
from api.domain.protocol.catalog import ServiceArea
from api.domain.protocol.status import ProtocolStage


class ProtocolService:
    def __init__(self, queries: ProtocolQueries, proposer: ProtocolProposer) -> None:
        self._queries = queries
        self._proposer = proposer

    async def list_services(self, area: ServiceArea | None) -> ToolResult[list[ServiceOfferDto]]:
        return await self._queries.list_services(area)

    async def list_protocols(
        self,
        status: ProtocolStage | None,
        service: str | None,
        period: str | None,
        page: PageRequest,
    ) -> ToolResult[list[ProtocolDto]]:
        return await self._queries.list_protocols(status, service, period, page)

    async def get_protocol(self, number: str) -> ToolResult[ProtocolDetailDto]:
        return await self._queries.get_protocol(number)

    async def propose_protocol(
        self, action: ProtocolAction, enrollment: str, subject: str | None
    ) -> ToolResult[Proposal]:
        return await self._proposer.propose(action, enrollment, subject)
