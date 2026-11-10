from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from operator import attrgetter

from api.domain.lms.exam import ExamAttempt, OnlineExam
from api.domain.shared.brand import Brand
from api.persistence.lms.models import LmsCourseRow, LmsQuizAttemptRow, LmsQuizRow
from api.persistence.lms.vocabulary import TENANT_BRAND, CourseLabel
from api.persistence.sag.catalog_models import SubjectRow

SECONDS_PER_MINUTE = 60


@dataclass(frozen=True, slots=True)
class ExamSources:
    courses: Sequence[LmsCourseRow]
    quizzes: Sequence[LmsQuizRow]
    attempts: Sequence[LmsQuizAttemptRow]
    subjects: Sequence[SubjectRow]


@dataclass(frozen=True, slots=True)
class ExamIndex:
    labels: dict[str, CourseLabel]
    brands: dict[str, Brand]
    names: dict[str, str]
    attempts: defaultdict[str, list[ExamAttempt]]


class ExamMapper:
    @classmethod
    def to_entities(cls, sources: ExamSources) -> list[OnlineExam]:
        index = cls._index(sources)
        exams = [
            cls._exam(quiz, index) for quiz in sources.quizzes if quiz.course_id in index.labels
        ]
        ordered = sorted(exams, key=cls._order)
        return sorted(ordered, key=attrgetter("term"), reverse=True)

    @staticmethod
    def _order(exam: OnlineExam) -> tuple[str, str, str]:
        return exam.subject_code, exam.kind.value, exam.quiz_id

    @classmethod
    def _index(cls, sources: ExamSources) -> ExamIndex:
        return ExamIndex(
            labels=CourseLabel.by_course(sources.courses),
            brands={row.id: TENANT_BRAND.from_source(row.tenant_id) for row in sources.courses},
            names={subject.code: subject.name for subject in sources.subjects},
            attempts=cls._attempts_by_quiz(sources.attempts),
        )

    @staticmethod
    def _exam(quiz: LmsQuizRow, index: ExamIndex) -> OnlineExam:
        label = index.labels[quiz.course_id]
        return OnlineExam(
            quiz_id=quiz.id,
            brand=index.brands[quiz.course_id],
            subject_code=label.subject_code,
            subject_name=index.names[label.subject_code],
            term=label.term,
            delivery=label.delivery,
            kind=quiz.kind,
            opens_at=quiz.time_open,
            closes_at=quiz.time_close,
            time_limit_minutes=int(quiz.time_limit) // SECONDS_PER_MINUTE,
            max_attempts=int(quiz.max_attempts),
            attempts=tuple(sorted(index.attempts[quiz.id], key=attrgetter("number"))),
        )

    @staticmethod
    def _attempts_by_quiz(
        rows: Sequence[LmsQuizAttemptRow],
    ) -> defaultdict[str, list[ExamAttempt]]:
        grouped: defaultdict[str, list[ExamAttempt]] = defaultdict(list)
        for row in rows:
            grouped[row.quiz_id].append(
                ExamAttempt(
                    number=int(row.number),
                    state=row.state,
                    started_at=row.time_start,
                    finished_at=row.time_finish,
                    grade=row.sum_grades,
                )
            )
        return grouped
