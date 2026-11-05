from api.application.dto.protocol_detail_dto import ProtocolDetailDto
from api.application.dto.protocol_dto import ProtocolDto
from api.application.dto.protocol_proposal_dto import Proposal
from api.application.dto.protocol_service_dto import ServiceDto
from api.application.dto.tool_result import ToolResult
from api.application.page import PageRequest
from api.application.protocol_proposer import ProtocolProposer
from api.application.protocol_queries import ProtocolQueries
from api.domain.protocol_catalog import ServiceArea
from api.domain.protocol_status import ProtocolStage


class ProtocolService:
    def __init__(self, queries: ProtocolQueries, proposer: ProtocolProposer) -> None:
        self._queries = queries
        self._proposer = proposer

    async def list_services(self, area: ServiceArea | None) -> ToolResult[list[ServiceDto]]:
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
        self, service: str, enrollment: str | None, message: str
    ) -> ToolResult[Proposal]:
        return await self._proposer.propose(service, enrollment, message)
