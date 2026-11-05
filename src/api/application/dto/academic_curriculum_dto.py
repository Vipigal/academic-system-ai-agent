from collections.abc import Iterable
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.application.dto.tool_result import StatedValue
from api.domain.academic_curriculum import CurriculumSubject, EnrollmentProgress
from api.domain.academic_record import SubjectResult


class PrerequisiteDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    name: str | None
    situation: StatedValue[SubjectResult]


class CurriculumSubjectDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    enrollment: str
    curriculum: str
    code: str
    name: str
    semester: int
    hours: int
    mandatory: bool
    situation: StatedValue[SubjectResult]
    prerequisite: PrerequisiteDto | None

    @classmethod
    def of(cls, progress: EnrollmentProgress, subject: CurriculumSubject) -> Self:
        return cls(
            enrollment=progress.enrollment.reference,
            curriculum=subject.curriculum_id,
            code=subject.code,
            name=subject.name,
            semester=subject.semester,
            hours=subject.hours,
            mandatory=subject.mandatory,
            situation=cls._situation(progress, subject.code),
            prerequisite=cls._prerequisite(progress, subject),
        )

    @classmethod
    def _prerequisite(
        cls, progress: EnrollmentProgress, subject: CurriculumSubject
    ) -> PrerequisiteDto | None:
        code = subject.prerequisite_code
        if code is None:
            return None
        return PrerequisiteDto(
            code=code,
            name=subject.prerequisite_name,
            situation=cls._situation(progress, code),
        )

    @staticmethod
    def _situation(progress: EnrollmentProgress, code: str) -> StatedValue[SubjectResult]:
        situation = progress.situation_of(code)
        if situation is None:
            return StatedValue[SubjectResult].not_recorded()
        return StatedValue[SubjectResult].recorded(situation)


class CurriculumTotals:
    @staticmethod
    def of(scoped: Iterable[EnrollmentProgress]) -> dict[str, Decimal | int]:
        totals: dict[str, Decimal | int] = {}
        for progress in scoped:
            prefix = progress.enrollment.reference
            totals[f"{prefix}.total_hours"] = progress.enrollment.curriculum_hours
            totals[f"{prefix}.completed_hours"] = progress.completed_hours
            totals[f"{prefix}.completion_pct"] = progress.completion_pct
            totals[f"{prefix}.pending_subjects"] = progress.pending_subjects
        return totals
