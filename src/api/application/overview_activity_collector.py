import asyncio

from api.application.academic_service import AcademicService
from api.application.dto.overview_pending_dto import PendingArea
from api.application.lms_service import LmsService
from api.application.overview_activity import ActivityRules
from api.application.overview_findings import Findings
from api.application.overview_pages import Gathered
from api.application.protocol_service import ProtocolService
from api.domain.protocol_status import ProtocolStage


class ActivityCollector:
    def __init__(
        self, academic: AcademicService, protocols: ProtocolService, lms: LmsService
    ) -> None:
        self._academic = academic
        self._protocols = protocols
        self._lms = lms

    async def collect(self) -> Findings:
        protocols, records, exams = await asyncio.gather(
            Gathered.of_pages(
                lambda page: self._protocols.list_protocols(
                    ProtocolStage.IN_PROGRESS, None, None, page
                )
            ),
            Gathered.of_pages(
                lambda page: self._academic.list_subject_records(None, None, None, page)
            ),
            Gathered.of_pages(lambda page: self._lms.list_online_exams(None, None, page)),
        )
        return Findings(
            {
                PendingArea.PROTOCOLS: ActivityRules.protocols(protocols.items),
                PendingArea.ATTENDANCE: ActivityRules.attendance(records.items),
                PendingArea.ONLINE_EXAMS: ActivityRules.exams(exams.items),
            },
            records.caveats + exams.caveats,
        )
