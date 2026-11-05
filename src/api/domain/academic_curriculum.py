from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Self

from api.domain.academic import Enrollment
from api.domain.academic_record import SubjectRecord, SubjectResult

COMPLETED_RESULTS = frozenset({SubjectResult.APPROVED, SubjectResult.EXEMPT})
RESULT_PRIORITY = (
    SubjectResult.APPROVED,
    SubjectResult.EXEMPT,
    SubjectResult.IN_PROGRESS,
    SubjectResult.FAILED,
    SubjectResult.FAILED_ATTENDANCE,
    SubjectResult.WITHDRAWN,
)
PERCENT_PRECISION = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class CurriculumSubject:
    curriculum_id: str
    code: str
    name: str
    hours: int
    semester: int
    mandatory: bool
    prerequisite_code: str | None
    prerequisite_name: str | None


@dataclass(frozen=True, slots=True)
class EnrollmentProgress:
    enrollment: Enrollment
    subjects: tuple[CurriculumSubject, ...]
    records: tuple[SubjectRecord, ...]
    results_by_subject: Mapping[str, frozenset[SubjectResult]]

    @classmethod
    def of(
        cls,
        enrollment: Enrollment,
        subjects: tuple[CurriculumSubject, ...],
        records: tuple[SubjectRecord, ...],
    ) -> Self:
        results: defaultdict[str, set[SubjectResult]] = defaultdict(set)
        for record in records:
            results[record.subject_code].add(record.result)
        frozen = {code: frozenset(found) for code, found in results.items()}
        return cls(enrollment, subjects, records, frozen)

    def situation_of(self, subject_code: str) -> SubjectResult | None:
        results = self.results_by_subject.get(subject_code, frozenset())
        return next((result for result in RESULT_PRIORITY if result in results), None)

    def is_completed(self, subject_code: str) -> bool:
        return self.situation_of(subject_code) in COMPLETED_RESULTS

    @property
    def completed_hours(self) -> int:
        return sum(subject.hours for subject in self.subjects if self.is_completed(subject.code))

    @property
    def completion_pct(self) -> Decimal:
        share = Decimal(self.completed_hours * 100) / self.enrollment.curriculum_hours
        return share.quantize(PERCENT_PRECISION, rounding=ROUND_HALF_UP)

    @property
    def pending_subjects(self) -> int:
        return sum(not self.is_completed(subject.code) for subject in self.subjects)
