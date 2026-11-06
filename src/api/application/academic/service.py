from api.application.academic.dto.catalog import (
    AcademicCalendarDto,
    CourseOfferDto,
    SubjectProfessorDto,
)
from api.application.academic.dto.curriculum import CurriculumSubjectDto, CurriculumTotals
from api.application.academic.dto.enrollment import EnrollmentDto
from api.application.academic.dto.record import SubjectRecordDto
from api.application.academic.records import SubjectRecordListing
from api.application.academic.scope import (
    AcademicCandidates,
    CalendarNotes,
    EnrollmentScope,
)
from api.application.shared.name_search import NameSearch
from api.application.shared.page import PageRequest
from api.application.shared.tool_result import ToolResult
from api.domain.ports.academic import AcademicCatalogRepository, StudentAcademicRepository
from api.domain.ports.clock import Clock
from api.domain.shared.brand import Modality


class AcademicService:
    def __init__(
        self,
        catalog: AcademicCatalogRepository,
        student: StudentAcademicRepository,
        clock: Clock,
    ) -> None:
        self._catalog = catalog
        self._student = student
        self._clock = clock

    async def get_academic_calendar(self, term: str | None) -> ToolResult[AcademicCalendarDto]:
        calendar = await self._catalog.get_calendar()
        selected = calendar.current if term is None else calendar.find(term)
        dto = AcademicCalendarDto.of(calendar, selected, self._clock.today())
        if term is None or selected is not None:
            return ToolResult.ok(dto)
        return ToolResult.ok(
            dto,
            caveats=CalendarNotes.caveats(calendar, term),
            coverage=CalendarNotes.coverage(calendar),
        )

    async def list_course_offers(
        self,
        course: str | None,
        modality: Modality | None,
        unit: str | None,
        page: PageRequest,
    ) -> ToolResult[list[CourseOfferDto]]:
        offers = await self._catalog.list_course_offers()
        courses = NameSearch.search(course, AcademicCandidates.of_courses(offers))
        if courses.missed:
            return ToolResult.not_found(courses.candidates)
        units = NameSearch.search(unit, AcademicCandidates.of_units(offers))
        if units.missed:
            return ToolResult.not_found(units.candidates)
        matched = [
            CourseOfferDto.from_entity(item)
            for item in offers
            if item.course_code in courses.codes
            and item.unit_id in units.codes
            and modality in {None, item.modality}
        ]
        return ToolResult.listing(page.paginate(matched))

    async def list_enrollments(self) -> ToolResult[list[EnrollmentDto]]:
        enrollments = await self._student.list_enrollments()
        calendar = await self._catalog.get_calendar()
        current = calendar.current.code
        return ToolResult.items([EnrollmentDto.from_entity(item, current) for item in enrollments])

    async def get_curriculum(
        self,
        enrollment: str | None,
        semester: int | None,
        subject: str | None,
        *,
        pending_only: bool,
        page: PageRequest,
    ) -> ToolResult[list[CurriculumSubjectDto]]:
        scope = EnrollmentScope.of(await self._student.list_progress(), enrollment)
        if scope.missed:
            return ToolResult.not_found(scope.candidates)
        search = NameSearch.search(subject, AcademicCandidates.of_matrix(scope.selected))
        if search.missed:
            return ToolResult.not_found(search.candidates)
        matched = [
            CurriculumSubjectDto.of(item, row)
            for item in scope.selected
            for row in item.subjects
            if row.code in search.codes
            and semester in {None, row.semester}
            and not (pending_only and item.is_completed(row.code))
        ]
        return ToolResult.listing(
            page.paginate(matched), totals=CurriculumTotals.of(scope.selected)
        )

    async def list_subject_records(
        self,
        enrollment: str | None,
        term: str | None,
        subject: str | None,
        page: PageRequest,
    ) -> ToolResult[list[SubjectRecordDto]]:
        scope = EnrollmentScope.of(await self._student.list_progress(), enrollment)
        if scope.missed:
            return ToolResult.not_found(scope.candidates)
        search = NameSearch.search(subject, AcademicCandidates.of_records(scope.records))
        if search.missed:
            return ToolResult.not_found(search.candidates)
        matched = (
            row
            for row in scope.records
            if row.subject_code in search.codes and term in {None, row.term.code}
        )
        return SubjectRecordListing.of(matched, self._clock.today(), page)

    async def list_subject_professors(
        self, subject: str, term: str | None
    ) -> ToolResult[list[SubjectProfessorDto]]:
        scope = EnrollmentScope.of(await self._student.list_progress(), None)
        search = NameSearch.search(
            subject,
            (
                *AcademicCandidates.of_matrix(scope.selected),
                *AcademicCandidates.of_records(scope.records),
            ),
        )
        if search.missed:
            return ToolResult.not_found(search.candidates)
        if search.is_ambiguous:
            return ToolResult.ambiguous(search.matched)
        calendar = await self._catalog.get_calendar()
        teachers = await self._catalog.list_subject_teachers(
            search.matched[0].code, term or calendar.current.code
        )
        own_classes = {row.class_id for row in scope.records}
        return ToolResult.items(SubjectProfessorDto.grouped(teachers, own_classes))
