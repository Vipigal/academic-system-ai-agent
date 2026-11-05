from api.application.dto.protocol_detail_dto import ProtocolDetailDto
from api.application.dto.protocol_dto import ProtocolDto
from api.application.dto.protocol_service_dto import ServiceDto
from api.application.dto.tool_result import ToolResult
from api.application.name_search import NameSearch
from api.application.page import PageRequest
from api.application.period_filter import PeriodFilter
from api.application.protocol_scope import ProtocolCandidates
from api.application.protocol_source import ProtocolSource
from api.domain.protocol_catalog import ServiceArea
from api.domain.protocol_proposal import ProtocolNumber
from api.domain.protocol_status import ProtocolStage


class ProtocolQueries:
    def __init__(self, source: ProtocolSource) -> None:
        self._source = source

    async def list_services(self, area: ServiceArea | None) -> ToolResult[list[ServiceDto]]:
        services = await self._source.services()
        return ToolResult.items(
            [ServiceDto.from_entity(item) for item in services if area in {None, item.area}]
        )

    async def list_protocols(
        self,
        status: ProtocolStage | None,
        service: str | None,
        period: str | None,
        page: PageRequest,
    ) -> ToolResult[list[ProtocolDto]]:
        snapshot = await self._source.snapshot()
        search = NameSearch.search(
            service, ProtocolCandidates.of_protocol_services(snapshot.protocols)
        )
        if search.missed:
            return ToolResult.not_found(search.candidates)
        matched = [
            item
            for item in snapshot.protocols
            if item.service.code in search.codes
            and status in {None, item.stage}
            and PeriodFilter.matches(period, item.opened_at.date().isoformat())
        ]
        return ToolResult.listing(
            page.paginate(snapshot.dtos(matched)), totals=snapshot.totals(matched)
        )

    async def get_protocol(self, number: str) -> ToolResult[ProtocolDetailDto]:
        snapshot = await self._source.snapshot()
        wanted = ProtocolNumber.digits(number)
        found = next((item for item in snapshot.protocols if item.number == wanted), None)
        if found is None:
            return ToolResult.not_found(ProtocolCandidates.of_protocols(snapshot.protocols))
        return ToolResult.ok(snapshot.detail(found))
