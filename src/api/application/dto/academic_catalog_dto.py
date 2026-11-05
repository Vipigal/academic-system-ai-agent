from collections.abc import Collection, Sequence
from datetime import date
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.application.dto.tool_result import StatedValue
from api.domain.academic import CourseOffer, Shift, SubjectTeacher
from api.domain.academic_calendar import AcademicCalendar, Term
from api.domain.brand import Modality


class TermDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    term: str
    start_date: date
    end_date: date
    av1_start: date
    av2_start: date
    is_current: bool

    @classmethod
    def from_entity(cls, term: Term) -> Self:
        return cls(
            term=term.code,
            start_date=term.start_date,
            end_date=term.end_date,
            av1_start=term.av1_start,
            av2_start=term.av2_start,
            is_current=term.is_current,
        )


class AcademicCalendarDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    reference_date: date
    term: StatedValue[TermDto]
    last_registered_term: TermDto

    @classmethod
    def of(cls, calendar: AcademicCalendar, selected: Term | None, reference: date) -> Self:
        stated: StatedValue[TermDto] = StatedValue.not_recorded()
        if selected is not None:
            stated = StatedValue.recorded(TermDto.from_entity(selected))
        return cls(
            reference_date=reference,
            term=stated,
            last_registered_term=TermDto.from_entity(calendar.last),
        )


class CourseOfferDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    course_code: str
    course_name: str
    unit_id: str
    unit_name: str
    city: str
    state: str
    shift: Shift
    modality: Modality

    @classmethod
    def from_entity(cls, offer: CourseOffer) -> Self:
        return cls(
            id=offer.id,
            course_code=offer.course_code,
            course_name=offer.course_name,
            unit_id=offer.unit_id,
            unit_name=offer.unit_name,
            city=offer.city,
            state=offer.state,
            shift=offer.shift,
            modality=offer.modality,
        )


class SubjectProfessorDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    email: str
    subject_code: str
    subject_name: str
    term: str
    unit_name: str | None
    teaches_student: bool

    @classmethod
    def grouped(
        cls, teachers: Sequence[SubjectTeacher], own_classes: Collection[str]
    ) -> list[Self]:
        own = {cls._key(row) for row in teachers if row.class_id in own_classes}
        unique = {cls._key(row): row for row in teachers}
        professors = [
            cls._from_entity(row, teaches_student=key in own) for key, row in unique.items()
        ]
        return sorted(professors, key=cls._sort_key)

    @staticmethod
    def _key(teacher: SubjectTeacher) -> tuple[str, str]:
        return teacher.email, teacher.unit_name or ""

    @classmethod
    def _from_entity(cls, teacher: SubjectTeacher, *, teaches_student: bool) -> Self:
        return cls(
            name=teacher.full_name,
            email=teacher.email,
            subject_code=teacher.subject_code,
            subject_name=teacher.subject_name,
            term=teacher.term,
            unit_name=teacher.unit_name,
            teaches_student=teaches_student,
        )

    def _sort_key(self) -> tuple[bool, str, str, str]:
        return not self.teaches_student, self.name, self.email, self.unit_name or ""
