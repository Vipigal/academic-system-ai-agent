import asyncio
from collections.abc import Sequence

from sqlalchemy import select

from api.domain.academic import CourseOffer, SubjectTeacher
from api.domain.academic_calendar import AcademicCalendar
from api.persistence.repository_adapter import RepositoryAdapter
from api.persistence.sag.catalog_models import (
    CourseOfferRow,
    CourseRow,
    SubjectRow,
    TermRow,
    UnitRow,
)
from api.persistence.sag.class_models import ClassSectionRow, ProfessorRow
from api.persistence.sag.mappers import CatalogMapper, TeacherMapper, TeacherSources


class SagAcademicCatalogRepository:
    def __init__(self, adapter: RepositoryAdapter) -> None:
        self._adapter = adapter

    async def get_calendar(self) -> AcademicCalendar:
        return CatalogMapper.calendar(await self._adapter.fetch(select(TermRow)))

    async def list_course_offers(self) -> Sequence[CourseOffer]:
        rows, courses, units = await asyncio.gather(
            self._adapter.fetch(
                select(CourseOfferRow).join(UnitRow, CourseOfferRow.unit_id == UnitRow.id)
            ),
            self._adapter.fetch(select(CourseRow)),
            self._adapter.fetch(select(UnitRow)),
        )
        return CatalogMapper.offers(rows, courses, units)

    async def list_subject_teachers(self, subject_code: str, term: str) -> Sequence[SubjectTeacher]:
        sources = await asyncio.gather(
            self._adapter.fetch(
                select(ClassSectionRow)
                .where(ClassSectionRow.subject_code == subject_code, ClassSectionRow.term == term)
                .order_by(ClassSectionRow.id)
            ),
            self._adapter.fetch(select(ProfessorRow)),
            self._adapter.fetch(select(UnitRow)),
            self._adapter.fetch(select(SubjectRow).where(SubjectRow.code == subject_code)),
        )
        return TeacherMapper.to_entities(TeacherSources(*sources))
