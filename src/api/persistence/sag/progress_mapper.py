from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from api.domain.academic.curriculum import CurriculumSubject, EnrollmentProgress
from api.domain.academic.enrollment import Enrollment
from api.domain.academic.record import Grades, SubjectRecord
from api.persistence.sag.catalog_models import CurriculumSubjectRow, SubjectRow, TermRow, UnitRow
from api.persistence.sag.class_models import ClassSectionRow, StudentClassRow
from api.persistence.sag.dialect import SagDialect
from api.persistence.sag.mappers import CatalogMapper, UnitNames
from api.persistence.sag.vocabulary import AcademicVocabulary, SourceColumn


@dataclass(frozen=True, slots=True)
class ProgressSources:
    curriculum: Sequence[CurriculumSubjectRow]
    classes: Sequence[StudentClassRow]
    sections: Sequence[ClassSectionRow]
    subjects: Sequence[SubjectRow]
    units: Sequence[UnitRow]
    terms: Sequence[TermRow]


class ProgressMapper:
    def __init__(self, sources: ProgressSources) -> None:
        self._subjects = {subject.code: subject for subject in sources.subjects}
        self._units = {unit.id: unit for unit in sources.units}
        self._sections = {section.id: section for section in sources.sections}
        self._terms = {term.code: term for term in CatalogMapper.calendar(sources.terms).terms}
        self._matrix: defaultdict[str, list[CurriculumSubject]] = defaultdict(list)
        for row in sources.curriculum:
            self._matrix[row.curriculum_id].append(self._curriculum_subject(row))
        self._records: defaultdict[str, list[SubjectRecord]] = defaultdict(list)
        for student_class in sources.classes:
            record = self._record(student_class)
            self._records[record.enrollment].append(record)

    def to_entity(self, enrollment: Enrollment) -> EnrollmentProgress:
        subjects = sorted(
            self._matrix[enrollment.curriculum_id],
            key=lambda subject: (subject.semester, subject.code),
        )
        return EnrollmentProgress.of(
            enrollment, tuple(subjects), tuple(self._records[enrollment.reference])
        )

    def _curriculum_subject(self, row: CurriculumSubjectRow) -> CurriculumSubject:
        subject = self._subjects[row.subject_code]
        prerequisite = row.prerequisite_code
        return CurriculumSubject(
            curriculum_id=row.curriculum_id,
            code=row.subject_code,
            name=subject.name,
            hours=int(subject.hours),
            semester=int(row.semester),
            mandatory=SourceColumn.is_yes(row.mandatory),
            prerequisite_code=prerequisite,
            prerequisite_name=None if prerequisite is None else self._subjects[prerequisite].name,
        )

    def _record(self, row: StudentClassRow) -> SubjectRecord:
        section = self._sections[row.class_id]
        return SubjectRecord(
            enrollment=SagDialect.reference(row.brand, row.student_id),
            class_id=row.class_id,
            term=self._terms[section.term],
            subject_code=section.subject_code,
            subject_name=self._subjects[section.subject_code].name,
            section=section.section,
            shift=AcademicVocabulary.shift(section.shift),
            delivery=AcademicVocabulary.delivery(section.delivery),
            unit_name=UnitNames.of(self._units, section.unit_id),
            is_retake=SourceColumn.is_yes(row.is_retake),
            grades=Grades(
                av1=SourceColumn.decimal(row.grade_av1),
                av2=SourceColumn.decimal(row.grade_av2),
                av3=SourceColumn.decimal(row.grade_av3),
                final=SourceColumn.decimal(row.final_grade),
            ),
            attendance_pct=SourceColumn.decimal(row.attendance_pct),
            result=AcademicVocabulary.result(row.result),
        )
