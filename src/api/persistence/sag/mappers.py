from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from api.domain.academic import CourseOffer, SubjectTeacher
from api.domain.academic_calendar import AcademicCalendar, Term
from api.persistence.sag.academic_vocabulary import AcademicVocabulary, SourceColumn
from api.persistence.sag.catalog_models import (
    CourseOfferRow,
    CourseRow,
    SubjectRow,
    TermRow,
    UnitRow,
)
from api.persistence.sag.class_models import ClassSectionRow, ProfessorRow


class UnitNames:
    @staticmethod
    def of(units: Mapping[str, UnitRow], unit_id: str | None) -> str | None:
        if unit_id is None:
            return None
        return units[unit_id].name


class CatalogMapper:
    @staticmethod
    def calendar(rows: Sequence[TermRow]) -> AcademicCalendar:
        return AcademicCalendar(
            tuple(
                Term(
                    code=row.code,
                    start_date=date.fromisoformat(row.start_date),
                    end_date=date.fromisoformat(row.end_date),
                    av1_start=date.fromisoformat(row.av1_start),
                    av2_start=date.fromisoformat(row.av2_start),
                    is_current=SourceColumn.is_yes(row.is_current),
                )
                for row in sorted(rows, key=lambda row: row.code)
            )
        )

    @staticmethod
    def offers(
        rows: Sequence[CourseOfferRow], courses: Sequence[CourseRow], units: Sequence[UnitRow]
    ) -> list[CourseOffer]:
        course_by_id = {course.id: course for course in courses}
        unit_by_id = {unit.id: unit for unit in units}
        offers = [
            CourseOffer(
                id=row.id,
                course_code=course_by_id[row.course_id].acronym,
                course_name=course_by_id[row.course_id].name,
                unit_id=row.unit_id,
                unit_name=unit_by_id[row.unit_id].name,
                city=unit_by_id[row.unit_id].city,
                state=unit_by_id[row.unit_id].state,
                shift=AcademicVocabulary.shift(row.shift),
            )
            for row in rows
        ]
        return sorted(offers, key=lambda offer: (offer.course_code, offer.unit_name, offer.id))


@dataclass(frozen=True, slots=True)
class TeacherSources:
    sections: Sequence[ClassSectionRow]
    professors: Sequence[ProfessorRow]
    units: Sequence[UnitRow]
    subjects: Sequence[SubjectRow]


class TeacherMapper:
    @staticmethod
    def to_entities(sources: TeacherSources) -> list[SubjectTeacher]:
        professor_by_id = {professor.id: professor for professor in sources.professors}
        unit_by_id = {unit.id: unit for unit in sources.units}
        subject_by_code = {subject.code: subject for subject in sources.subjects}
        return [
            SubjectTeacher(
                class_id=section.id,
                subject_code=section.subject_code,
                subject_name=subject_by_code[section.subject_code].name,
                term=section.term,
                full_name=professor_by_id[section.professor_id].full_name,
                email=professor_by_id[section.professor_id].email,
                unit_name=UnitNames.of(unit_by_id, section.unit_id),
            )
            for section in sources.sections
        ]
