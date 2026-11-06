import asyncio
from collections.abc import Sequence

from sqlalchemy import select

from api.domain.academic.curriculum import EnrollmentProgress
from api.domain.academic.enrollment import Enrollment
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.sag.catalog_models import (
    CourseRow,
    CurriculumRow,
    CurriculumSubjectRow,
    SubjectRow,
    TermRow,
    UnitRow,
)
from api.persistence.sag.class_models import ClassSectionRow, StudentClassRow
from api.persistence.sag.enrollment_mapper import EnrollmentMapper, EnrollmentSources
from api.persistence.sag.models import EnrollmentHistoryRow, EnrollmentRow, TermEnrollmentRow
from api.persistence.sag.progress_mapper import ProgressMapper, ProgressSources


class SagStudentAcademicRepository:
    def __init__(self, adapter: RepositoryAdapter) -> None:
        self._adapter = adapter

    async def list_enrollments(self) -> Sequence[Enrollment]:
        rows = await self._adapter.fetch(
            select(EnrollmentRow).order_by(EnrollmentRow.brand, EnrollmentRow.student_id)
        )
        sources = await asyncio.gather(
            self._adapter.fetch(select(CourseRow)),
            self._adapter.fetch(select(UnitRow)),
            self._adapter.fetch(select(CurriculumRow)),
            self._adapter.fetch(select(TermEnrollmentRow)),
            self._adapter.fetch(
                select(EnrollmentHistoryRow).order_by(
                    EnrollmentHistoryRow.event_date, EnrollmentHistoryRow.id
                )
            ),
        )
        mapper = EnrollmentMapper(EnrollmentSources(*sources))
        return [mapper.to_entity(row) for row in rows]

    async def list_progress(self) -> Sequence[EnrollmentProgress]:
        enrollments = await self.list_enrollments()
        curricula = {enrollment.curriculum_id for enrollment in enrollments}
        sources = await asyncio.gather(
            self._adapter.fetch(
                select(CurriculumSubjectRow).where(
                    CurriculumSubjectRow.curriculum_id.in_(curricula)
                )
            ),
            self._adapter.fetch(select(StudentClassRow)),
            self._adapter.fetch(
                select(ClassSectionRow).join(
                    StudentClassRow, StudentClassRow.class_id == ClassSectionRow.id
                )
            ),
            self._adapter.fetch(select(SubjectRow)),
            self._adapter.fetch(select(UnitRow)),
            self._adapter.fetch(select(TermRow)),
        )
        mapper = ProgressMapper(ProgressSources(*sources))
        return [mapper.to_entity(enrollment) for enrollment in enrollments]
