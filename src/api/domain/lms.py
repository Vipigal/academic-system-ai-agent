from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from api.domain.academic_record import Delivery
from api.domain.brand import Brand

LMS_RECORDS_START = date(2023, 2, 1)


class ExamKind(Enum):
    AV1 = "av1"
    AV2 = "av2"
    PRACTICE_TEST = "practice_test"


class AttemptState(Enum):
    FINISHED = "finished"
    ABANDONED = "abandoned"


class ExamWindow(Enum):
    NOT_OPEN = "not_open"
    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class ExamAttempt:
    number: int
    state: AttemptState
    started_at: datetime
    finished_at: datetime | None
    grade: Decimal | None


@dataclass(frozen=True, slots=True)
class OnlineExam:
    quiz_id: str
    brand: Brand
    subject_code: str
    subject_name: str
    term: str
    delivery: Delivery
    kind: ExamKind
    opens_at: datetime
    closes_at: datetime
    time_limit_minutes: int
    max_attempts: int
    attempts: tuple[ExamAttempt, ...]

    @property
    def attempts_used(self) -> int:
        return max((attempt.number for attempt in self.attempts), default=0)

    @property
    def attempts_remaining(self) -> int:
        return max(self.max_attempts - self.attempts_used, 0)

    @property
    def has_abandoned_attempt(self) -> bool:
        return any(attempt.state is AttemptState.ABANDONED for attempt in self.attempts)

    @property
    def latest_grade(self) -> Decimal | None:
        finished = [attempt for attempt in self.attempts if attempt.state is AttemptState.FINISHED]
        return finished[-1].grade if finished else None

    def window_on(self, today: date) -> ExamWindow:
        if today < self.opens_at.date():
            return ExamWindow.NOT_OPEN
        if today > self.closes_at.date():
            return ExamWindow.CLOSED
        return ExamWindow.OPEN
