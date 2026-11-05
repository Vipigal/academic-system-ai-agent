from api.application.academic_service import AcademicService
from api.application.dto.academic_record_dto import SubjectRecordDto
from api.application.dto.lms_exam_dto import OnlineExamDto
from api.application.dto.overview_pending_dto import PendingArea
from api.application.dto.protocol_dto import ProtocolDto
from api.application.lms_service import LmsService
from api.application.overview_activity import ActivityRules
from api.application.overview_findings import Findings
from api.application.overview_pages import Gathered, Listing
from api.application.page import PageRequest
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
        protocols = await Gathered.of_pages(self._protocol_page)
        records = await Gathered.of_pages(self._record_page)
        exams = await Gathered.of_pages(self._exam_page)
        return Findings(
            {
                PendingArea.PROTOCOLS: ActivityRules.protocols(protocols.items),
                PendingArea.ATTENDANCE: ActivityRules.attendance(records.items),
                PendingArea.ONLINE_EXAMS: ActivityRules.exams(exams.items),
            },
            records.caveats + exams.caveats,
        )

    async def _protocol_page(self, page: PageRequest) -> Listing[ProtocolDto]:
        return await self._protocols.list_protocols(ProtocolStage.IN_PROGRESS, None, None, page)

    async def _record_page(self, page: PageRequest) -> Listing[SubjectRecordDto]:
        return await self._academic.list_subject_records(None, None, None, page)

    async def _exam_page(self, page: PageRequest) -> Listing[OnlineExamDto]:
        return await self._lms.list_online_exams(None, None, page)
