from datetime import date, datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.application.shared.tool_result import StatedValue
from api.domain.academic.record import Delivery
from api.domain.lms.exam import AttemptState, ExamAttempt, ExamKind, ExamWindow, OnlineExam


class ExamAttemptDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: int
    state: AttemptState
    started_at: datetime
    finished_at: datetime | None
    grade: Decimal | None

    @classmethod
    def from_entity(cls, attempt: ExamAttempt) -> Self:
        return cls(
            number=attempt.number,
            state=attempt.state,
            started_at=attempt.started_at,
            finished_at=attempt.finished_at,
            grade=attempt.grade,
        )


class OnlineExamDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    subject_code: str
    subject_name: str
    term: str
    delivery: Delivery
    kind: ExamKind
    opens_at: datetime
    closes_at: datetime
    window: ExamWindow
    time_limit_minutes: int
    max_attempts: int
    attempts_used: int
    attempts_remaining: int
    attempts: list[ExamAttemptDto]
    ava_grade: Decimal | None
    official_grade: StatedValue[Decimal] | None

    @classmethod
    def from_entity(
        cls, exam: OnlineExam, today: date, official_grade: StatedValue[Decimal] | None
    ) -> Self:
        return cls(
            subject_code=exam.subject_code,
            subject_name=exam.subject_name,
            term=exam.term,
            delivery=exam.delivery,
            kind=exam.kind,
            opens_at=exam.opens_at,
            closes_at=exam.closes_at,
            window=exam.window_on(today),
            time_limit_minutes=exam.time_limit_minutes,
            max_attempts=exam.max_attempts,
            attempts_used=exam.attempts_used,
            attempts_remaining=exam.attempts_remaining,
            attempts=[ExamAttemptDto.from_entity(attempt) for attempt in exam.attempts],
            ava_grade=exam.latest_grade,
            official_grade=official_grade,
        )
