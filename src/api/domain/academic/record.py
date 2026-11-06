from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

from api.domain.academic.enrollment import Shift
from api.domain.academic.term_calendar import Term

AV1_WEIGHT = Decimal("0.4")
AV2_WEIGHT = Decimal("0.6")
PASSING_AVERAGE = Decimal(6)
ATTENDANCE_LIMIT = Decimal(75)
GRADE_PRECISION = Decimal("0.1")


class SubjectResult(Enum):
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    FAILED = "failed"
    FAILED_ATTENDANCE = "failed_attendance"
    WITHDRAWN = "withdrawn"
    EXEMPT = "exempt"


class Delivery(Enum):
    IN_PERSON = "in_person"
    ONLINE = "online"
    EXEMPTION = "exemption"


NO_GRADES_EXPECTED = frozenset({SubjectResult.EXEMPT, SubjectResult.WITHDRAWN})


@dataclass(frozen=True, slots=True)
class Grades:
    av1: Decimal | None
    av2: Decimal | None
    av3: Decimal | None
    final: Decimal | None


@dataclass(frozen=True, slots=True)
class SubjectRecord:
    enrollment: str
    class_id: str
    term: Term
    subject_code: str
    subject_name: str
    section: str
    shift: Shift
    delivery: Delivery
    unit_name: str | None
    is_retake: bool
    grades: Grades
    attendance_pct: Decimal | None
    result: SubjectResult

    def grade_is_awaited(self, expected: date, reference: date) -> bool:
        return self.result not in NO_GRADES_EXPECTED and reference < expected

    def required_av2(self) -> Decimal | None:
        av1 = self.grades.av1
        if self.result is not SubjectResult.IN_PROGRESS or av1 is None:
            return None
        needed = (PASSING_AVERAGE - AV1_WEIGHT * av1) / AV2_WEIGHT
        return needed.quantize(GRADE_PRECISION, rounding=ROUND_HALF_UP)

    def uses_av_rule(self, reference: date) -> bool:
        if self.grades.av3 is not None:
            return True
        return self.grades.av2 is None and self.grade_is_awaited(self.term.av2_start, reference)

    @property
    def uses_attendance_rule(self) -> bool:
        if self.attendance_pct is None:
            return self.delivery is Delivery.ONLINE
        return self.attendance_pct <= ATTENDANCE_LIMIT
