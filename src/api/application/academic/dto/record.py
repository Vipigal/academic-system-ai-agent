from datetime import date
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.application.shared.tool_result import StatedValue
from api.domain.academic.enrollment import Shift
from api.domain.academic.record import Delivery, SubjectRecord, SubjectResult


class SubjectRecordDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    enrollment: str
    class_id: str
    term: str
    subject_code: str
    subject_name: str
    section: str
    shift: Shift
    delivery: Delivery
    unit_name: str | None
    is_retake: bool
    av1: StatedValue[Decimal]
    av2: StatedValue[Decimal]
    av3: StatedValue[Decimal]
    final_grade: StatedValue[Decimal]
    attendance_pct: StatedValue[Decimal]
    result: SubjectResult
    required_av2: StatedValue[Decimal]

    @classmethod
    def from_entity(cls, record: SubjectRecord, reference: date) -> Self:
        term = record.term
        grades = record.grades
        return cls(
            enrollment=record.enrollment,
            class_id=record.class_id,
            term=term.code,
            subject_code=record.subject_code,
            subject_name=record.subject_name,
            section=record.section,
            shift=record.shift,
            delivery=record.delivery,
            unit_name=record.unit_name,
            is_retake=record.is_retake,
            av1=cls._grade(record, grades.av1, term.av1_start, reference),
            av2=cls._grade(record, grades.av2, term.av2_start, reference),
            av3=cls._grade(record, grades.av3, term.end_date, reference),
            final_grade=cls._grade(record, grades.final, term.end_date, reference),
            attendance_pct=cls._stated(record.attendance_pct),
            result=record.result,
            required_av2=cls._stated(record.required_av2()),
        )

    @classmethod
    def _grade(
        cls, record: SubjectRecord, grade: Decimal | None, expected: date, reference: date
    ) -> StatedValue[Decimal]:
        if grade is None and record.grade_is_awaited(expected, reference):
            return StatedValue[Decimal].not_yet()
        return cls._stated(grade)

    @staticmethod
    def _stated(value: Decimal | None) -> StatedValue[Decimal]:
        if value is None:
            return StatedValue[Decimal].not_recorded()
        return StatedValue[Decimal].recorded(value)
