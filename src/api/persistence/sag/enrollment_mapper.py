from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from api.domain.academic.enrollment import Enrollment, StatusChange, TermStatus
from api.persistence.sag.catalog_models import CourseRow, CurriculumRow, UnitRow
from api.persistence.sag.dialect import SagDialect
from api.persistence.sag.models import EnrollmentHistoryRow, EnrollmentRow, TermEnrollmentRow


@dataclass(frozen=True, slots=True)
class EnrollmentSources:
    courses: Sequence[CourseRow]
    units: Sequence[UnitRow]
    curricula: Sequence[CurriculumRow]
    registrations: Sequence[TermEnrollmentRow]
    history: Sequence[EnrollmentHistoryRow]


class EnrollmentMapper:
    def __init__(self, sources: EnrollmentSources) -> None:
        self._courses = {course.id: course for course in sources.courses}
        self._units = {unit.id: unit for unit in sources.units}
        self._hours = {row.id: int(row.total_hours) for row in sources.curricula}
        self._registered: defaultdict[str, dict[str, TermStatus]] = defaultdict(dict)
        for registration in sources.registrations:
            registered = self._registered[
                SagDialect.reference(registration.brand, registration.student_id)
            ]
            registered[registration.term] = registration.term_status
        self._changes: defaultdict[str, list[StatusChange]] = defaultdict(list)
        for event in sources.history:
            key = SagDialect.reference(event.brand, event.student_id)
            self._changes[key].append(self._change(event))

    def to_entity(self, row: EnrollmentRow) -> Enrollment:
        reference = SagDialect.reference(row.brand, row.student_id)
        course = self._courses[row.course_id]
        return Enrollment(
            reference=reference,
            brand=SagDialect.enrollment_ref(row.brand, row.student_id).brand,
            course_code=course.acronym,
            course_name=course.name,
            curriculum_id=row.curriculum_id,
            curriculum_hours=self._hours[row.curriculum_id],
            unit_name=self._units[row.unit_id].name,
            modality=row.modality,
            shift=row.shift,
            status=row.status,
            status_date=row.status_date,
            entry_term=row.entry_term,
            semester=int(row.semester),
            completion_pct=row.completion_pct,
            gpa=row.gpa,
            origin_reference=self._origin(row),
            registrations=self._registered[reference],
            history=tuple(self._changes[reference]),
        )

    @staticmethod
    def _origin(row: EnrollmentRow) -> str | None:
        if row.origin_brand is None or row.origin_student_id is None:
            return None
        return SagDialect.reference(row.origin_brand, row.origin_student_id)

    @staticmethod
    def _change(event: EnrollmentHistoryRow) -> StatusChange:
        return StatusChange(
            event_date=event.event_date,
            term=event.term,
            previous=event.old_status,
            current=event.new_status,
            reason=event.reason,
        )
