from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.application.shared.tool_result import StatedValue
from api.domain.academic.course import CourseNames
from api.domain.academic.enrollment import (
    Enrollment,
    EnrollmentStatus,
    Shift,
    StatusChange,
    TermStatus,
)
from api.domain.shared.brand import Brand, Modality


class StatusChangeDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_date: date
    term: str
    previous_status: EnrollmentStatus | None
    new_status: EnrollmentStatus
    reason: str

    @classmethod
    def from_entity(cls, change: StatusChange) -> Self:
        return cls(
            event_date=change.event_date,
            term=change.term,
            previous_status=change.previous,
            new_status=change.current,
            reason=change.reason,
        )


class EnrollmentDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    enrollment: str
    brand: Brand
    course_code: str
    course_name: str
    course_name_pt: str | None
    curriculum: str
    unit_name: str
    modality: Modality
    shift: Shift
    status: EnrollmentStatus
    status_date: date
    entry_term: str
    semester: int
    cr: StatedValue[Decimal]
    completion_pct: Decimal
    current_term: str
    current_term_registration: StatedValue[TermStatus]
    transferred_from: str | None
    history: list[StatusChangeDto]

    @classmethod
    def from_entity(cls, enrollment: Enrollment, current_term: str) -> Self:
        return cls(
            enrollment=enrollment.reference,
            brand=enrollment.brand,
            course_code=enrollment.course_code,
            course_name=enrollment.course_name,
            course_name_pt=CourseNames.portuguese(enrollment.course_code),
            curriculum=enrollment.curriculum_id,
            unit_name=enrollment.unit_name,
            modality=enrollment.modality,
            shift=enrollment.shift,
            status=enrollment.status,
            status_date=enrollment.status_date,
            entry_term=enrollment.entry_term,
            semester=enrollment.semester,
            cr=cls._cr(enrollment.gpa),
            completion_pct=enrollment.completion_pct,
            current_term=current_term,
            current_term_registration=cls._registration(enrollment, current_term),
            transferred_from=enrollment.origin_reference,
            history=[StatusChangeDto.from_entity(change) for change in enrollment.history],
        )

    @staticmethod
    def _cr(gpa: Decimal | None) -> StatedValue[Decimal]:
        if gpa is None:
            return StatedValue[Decimal].not_recorded()
        return StatedValue[Decimal].recorded(gpa)

    @staticmethod
    def _registration(enrollment: Enrollment, term: str) -> StatedValue[TermStatus]:
        status = enrollment.registrations.get(term)
        if status is None:
            return StatedValue[TermStatus].not_recorded()
        return StatedValue[TermStatus].recorded(status)
