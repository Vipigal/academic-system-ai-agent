from itertools import chain, starmap

from api.application.academic.service import AcademicService
from api.application.finance.service import FinancialService
from api.application.lms.service import LmsService
from api.application.overview.caveats import OverviewCaveats
from api.application.overview.dto.pending import (
    AttentionItemDto,
    CheckedItemDto,
    CheckSituation,
    PendingArea,
    PendingItemsDto,
)
from api.application.overview.findings import Found
from api.application.overview.pending_collector import PendingCollector
from api.application.protocol.service import ProtocolService
from api.application.shared.tool_result import ToolResult
from api.domain.ports.clock import Clock


class OverviewService:
    def __init__(
        self,
        academic: AcademicService,
        financial: FinancialService,
        protocols: ProtocolService,
        lms: LmsService,
        clock: Clock,
    ) -> None:
        self._collector = PendingCollector(academic, financial, protocols, lms, clock)
        self._clock = clock

    async def get_pending_items(self) -> ToolResult[PendingItemsDto]:
        findings = await self._collector.collect()
        found = findings.found
        return ToolResult.ok(
            self._dto(found),
            totals=self._totals(found),
            caveats=OverviewCaveats.declared(findings.caveats),
        )

    def _dto(self, found: Found) -> PendingItemsDto:
        return PendingItemsDto(
            reference_date=self._clock.today().isoformat(),
            checked=tuple(starmap(self._checked, found.items())),
            attention=tuple(chain.from_iterable(found.values())),
        )

    @staticmethod
    def _checked(area: PendingArea, items: list[AttentionItemDto]) -> CheckedItemDto:
        return CheckedItemDto(
            area=area,
            situation=CheckSituation.ATTENTION if items else CheckSituation.OK,
            attention_count=len(items),
        )

    @staticmethod
    def _totals(found: Found) -> dict[str, int]:
        return {area.value: len(items) for area, items in found.items()}
