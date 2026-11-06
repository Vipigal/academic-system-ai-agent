import asyncio

from api.application.academic.service import AcademicService
from api.application.finance.service import FinancialService
from api.application.lms.service import LmsService
from api.application.overview.activity_collector import ActivityCollector
from api.application.overview.findings import Findings
from api.application.overview.standing_collector import StandingCollector
from api.application.protocol.service import ProtocolService
from api.domain.ports.clock import Clock


class PendingCollector:
    def __init__(
        self,
        academic: AcademicService,
        financial: FinancialService,
        protocols: ProtocolService,
        lms: LmsService,
        clock: Clock,
    ) -> None:
        self._standing = StandingCollector(academic, financial, clock)
        self._activity = ActivityCollector(academic, protocols, lms)

    async def collect(self) -> Findings:
        standing, activity = await asyncio.gather(
            self._standing.collect(), self._activity.collect()
        )
        return Findings({**standing.found, **activity.found}, standing.caveats + activity.caveats)
