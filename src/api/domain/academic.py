from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from api.domain.brand import Brand, Modality


class Shift(Enum):
    MORNING = "morning"
    EVENING = "evening"
    ONLINE = "online"


class EnrollmentStatus(Enum):
    ACTIVE = "active"
    LOCKED = "locked"
    CANCELLED = "cancelled"
    DROPOUT = "dropout"
    TRANSFERRED = "transferred"
    GRADUATED = "graduated"


class TermStatus(Enum):
    REGISTERED = "registered"
    LOCKED = "locked"
    NOT_RENEWED = "not_renewed"


@dataclass(frozen=True, slots=True)
class CourseOffer:
    id: str
    course_code: str
    course_name: str
    unit_id: str
    unit_name: str
    city: str
    state: str
    shift: Shift

    @property
    def modality(self) -> Modality:
        return Modality.ONLINE if self.shift is Shift.ONLINE else Modality.IN_PERSON


@dataclass(frozen=True, slots=True)
class StatusChange:
    event_date: date
    term: str
    previous: EnrollmentStatus | None
    current: EnrollmentStatus
    reason: str


@dataclass(frozen=True, slots=True)
class Enrollment:
    reference: str
    brand: Brand
    course_code: str
    course_name: str
    curriculum_id: str
    curriculum_hours: int
    unit_name: str
    modality: Modality
    shift: Shift
    status: EnrollmentStatus
    status_date: date
    entry_term: str
    semester: int
    completion_pct: Decimal
    gpa: Decimal | None
    origin_reference: str | None
    registrations: Mapping[str, TermStatus]
    history: tuple[StatusChange, ...]


@dataclass(frozen=True, slots=True)
class SubjectTeacher:
    class_id: str
    subject_code: str
    subject_name: str
    term: str
    full_name: str
    email: str
    unit_name: str | None
