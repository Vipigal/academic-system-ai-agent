from collections.abc import Iterable, Sequence
from datetime import date
from decimal import Decimal

from api.application.shared.tool_result import Candidate, Caveat, Coverage, StatedValue
from api.domain.academic.curriculum import EnrollmentProgress
from api.domain.academic.record import SubjectRecord
from api.domain.academic.term_calendar import AcademicCalendar
from api.domain.lms.account import LmsAccount
from api.domain.lms.exam import LMS_RECORDS_START, ExamKind, OnlineExam
from api.domain.ontology.lms import SUSPENSAO_DO_AVA, TENTATIVA, ULTIMO_ACESSO
from api.domain.shared.brand import Brand

type RecordIndex = dict[tuple[Brand, str, str], SubjectRecord]
COVERAGE_NOTE = "O ambiente virtual só tem registros a partir desta data."


class LmsCandidates:
    @classmethod
    def exams_matching(
        cls, exams: Iterable[OnlineExam], codes: frozenset[str], term: str | None
    ) -> list[OnlineExam]:
        return [exam for exam in exams if cls._matches(exam, codes, term)]

    @staticmethod
    def _matches(exam: OnlineExam, codes: frozenset[str], term: str | None) -> bool:
        return exam.subject_code in codes and term in {None, exam.term}

    @staticmethod
    def of_subjects(items: Iterable[tuple[str, str]]) -> Iterable[Candidate]:
        return (Candidate(code=code, name=name) for code, name in items)

    @staticmethod
    def of_exams(exams: Iterable[OnlineExam]) -> Iterable[Candidate]:
        return LmsCandidates.of_subjects((exam.subject_code, exam.subject_name) for exam in exams)


class LmsCoverage:
    @classmethod
    def for_term(
        cls, term: str | None, calendar: AcademicCalendar, *, found: bool
    ) -> Coverage | None:
        if cls._starts_before_records(term, calendar) or (term is None and not found):
            return Coverage(from_date=LMS_RECORDS_START, note=COVERAGE_NOTE)
        return None

    @staticmethod
    def _starts_before_records(term: str | None, calendar: AcademicCalendar) -> bool:
        if term is None:
            return False
        known = calendar.find(term)
        if known is None:
            return term < calendar.first.code
        return known.start_date < LMS_RECORDS_START


class ExamNotes:
    @staticmethod
    def caveats(exams: Sequence[OnlineExam]) -> tuple[Caveat, ...]:
        if any(exam.has_abandoned_attempt for exam in exams):
            return (Caveat.from_ontology(TENTATIVA),)
        return ()


class AccountNotes:
    @staticmethod
    def caveats(accounts: Sequence[LmsAccount]) -> tuple[Caveat, ...]:
        notes: list[Caveat] = []
        if any(account.never_accessed for account in accounts):
            notes.append(Caveat.from_ontology(ULTIMO_ACESSO))
        if any(account.suspended for account in accounts):
            notes.append(Caveat.from_ontology(SUSPENSAO_DO_AVA))
        return tuple(notes)


class OfficialGrades:
    @staticmethod
    def records_by_class(
        progress: Iterable[EnrollmentProgress],
    ) -> RecordIndex:
        return {
            (item.enrollment.brand, record.subject_code, record.term.code): record
            for item in progress
            for record in item.records
        }

    @classmethod
    def of(
        cls, exam: OnlineExam, records: RecordIndex, reference: date
    ) -> StatedValue[Decimal] | None:
        record = records.get((exam.brand, exam.subject_code, exam.term))
        if record is None or exam.kind is ExamKind.PRACTICE_TEST:
            return None
        grade, expected = cls._grade_and_date(record, exam.kind)
        if grade is not None:
            return StatedValue[Decimal].recorded(grade)
        if record.grade_is_awaited(expected, reference):
            return StatedValue[Decimal].not_yet()
        return StatedValue[Decimal].not_recorded()

    @staticmethod
    def _grade_and_date(record: SubjectRecord, kind: ExamKind) -> tuple[Decimal | None, date]:
        if kind is ExamKind.AV1:
            return record.grades.av1, record.term.av1_start
        return record.grades.av2, record.term.av2_start
