from api.application.dto.lms_account_dto import LmsAccountDto
from api.application.dto.lms_exam_dto import OnlineExamDto
from api.application.dto.lms_material_dto import MaterialViewDto
from api.application.dto.tool_result import Candidate, Caveat, ToolResult
from api.application.lms_scope import ExamNotes, LmsCandidates, LmsCoverage, OfficialGrades
from api.application.name_search import NameSearch
from api.application.page import Page, PageRequest
from api.domain.lms import OnlineExam
from api.domain.ontology.lms import SUSPENSAO_DO_AVA, ULTIMO_ACESSO
from api.domain.ports.academic import AcademicCatalogRepository, StudentAcademicRepository
from api.domain.ports.clock import Clock
from api.domain.ports.lms import LmsRepository


class LmsService:
    def __init__(
        self,
        lms: LmsRepository,
        catalog: AcademicCatalogRepository,
        student: StudentAcademicRepository,
        clock: Clock,
    ) -> None:
        self._lms = lms
        self._catalog = catalog
        self._student = student
        self._clock = clock

    async def list_online_exams(
        self, subject: str | None, term: str | None, page: PageRequest
    ) -> ToolResult[list[OnlineExamDto]]:
        exams = await self._lms.list_exams()
        search = NameSearch.search(subject, LmsCandidates.of_exams(exams))
        if search.missed:
            return ToolResult.not_found(search.candidates)
        return await self._exam_listing(
            LmsCandidates.exams_matching(exams, search.codes, term), term, page
        )

    async def get_lms_account(self) -> ToolResult[list[LmsAccountDto]]:
        accounts = await self._lms.list_accounts()
        caveats: list[Caveat] = []
        if any(account.never_accessed for account in accounts):
            caveats.append(Caveat.from_ontology(ULTIMO_ACESSO))
        if any(account.suspended for account in accounts):
            caveats.append(Caveat.from_ontology(SUSPENSAO_DO_AVA))
        return ToolResult.items(
            [LmsAccountDto.from_entity(account) for account in accounts],
            caveats=tuple(caveats),
        )

    async def list_material_views(
        self, subject: str, query: str | None, page: PageRequest
    ) -> ToolResult[list[MaterialViewDto]]:
        materials = await self._lms.list_materials()
        search = NameSearch.search(
            subject,
            LmsCandidates.of_subjects((item.subject_code, item.subject_name) for item in materials),
        )
        if search.missed:
            return ToolResult.not_found(search.candidates)
        of_subject = [item for item in materials if item.subject_code in search.codes]
        names = NameSearch.search(
            query, (Candidate(code=item.name, name=item.name) for item in of_subject)
        )
        if names.missed:
            return ToolResult.not_found(names.candidates)
        matched = [item for item in of_subject if item.name in names.codes]
        return ToolResult.listing(
            page.paginate([MaterialViewDto.from_entity(item) for item in matched])
        )

    async def _exam_listing(
        self, matched: list[OnlineExam], term: str | None, page: PageRequest
    ) -> ToolResult[list[OnlineExamDto]]:
        paged = page.paginate(matched)
        coverage = LmsCoverage.for_term(
            term, await self._catalog.get_calendar(), found=bool(matched)
        )
        return ToolResult.listing(
            Page(tuple(await self._dtos_of(paged.items)), paged.info),
            caveats=ExamNotes.caveats(matched),
            coverage=coverage,
        )

    async def _dtos_of(self, exams: tuple[OnlineExam, ...]) -> list[OnlineExamDto]:
        today = self._clock.today()
        records = OfficialGrades.records_by_class(await self._student.list_progress())
        return [
            OnlineExamDto.from_entity(exam, today, OfficialGrades.of(exam, records, today))
            for exam in exams
        ]
