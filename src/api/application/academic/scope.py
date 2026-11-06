from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Self

from api.application.shared.tool_result import Candidate, Caveat, Coverage
from api.domain.academic.curriculum import EnrollmentProgress
from api.domain.academic.enrollment import CourseOffer
from api.domain.academic.record import SubjectRecord
from api.domain.academic.term_calendar import AcademicCalendar
from api.domain.ontology.academic_enrollment import CALENDARIO_2027

CALENDAR_COVERAGE_NOTE = "O calendário só tem os semestres cadastrados a partir desta data."


@dataclass(frozen=True, slots=True)
class EnrollmentScope:
    missed: bool
    selected: tuple[EnrollmentProgress, ...]
    candidates: tuple[Candidate, ...]

    @classmethod
    def of(cls, progress: Sequence[EnrollmentProgress], reference: str | None) -> Self:
        selected = tuple(
            item for item in progress if reference in {None, item.enrollment.reference}
        )
        return cls(
            missed=reference is not None and not selected,
            selected=selected,
            candidates=tuple(
                Candidate(code=item.enrollment.reference, name=item.enrollment.course_name)
                for item in progress
            ),
        )

    @property
    def records(self) -> list[SubjectRecord]:
        return [record for item in self.selected for record in item.records]


class AcademicCandidates:
    @staticmethod
    def of_courses(offers: Iterable[CourseOffer]) -> Iterable[Candidate]:
        return (Candidate(code=item.course_code, name=item.course_name) for item in offers)

    @staticmethod
    def of_units(offers: Iterable[CourseOffer]) -> Iterable[Candidate]:
        return (Candidate(code=item.unit_id, name=item.unit_name) for item in offers)

    @staticmethod
    def of_matrix(progress: Iterable[EnrollmentProgress]) -> Iterable[Candidate]:
        return (
            Candidate(code=subject.code, name=subject.name)
            for item in progress
            for subject in item.subjects
        )

    @staticmethod
    def of_records(records: Iterable[SubjectRecord]) -> Iterable[Candidate]:
        return (Candidate(code=item.subject_code, name=item.subject_name) for item in records)


class CalendarNotes:
    @staticmethod
    def coverage(calendar: AcademicCalendar) -> Coverage:
        return Coverage(from_date=calendar.first.start_date, note=CALENDAR_COVERAGE_NOTE)

    @staticmethod
    def caveats(calendar: AcademicCalendar, term: str) -> tuple[Caveat, ...]:
        if calendar.is_after_last(term):
            return (Caveat.from_ontology(CALENDARIO_2027),)
        return ()
