from sqlalchemy import select, tuple_

from api.persistence.core.ownership import PUBLIC, OwnershipMap
from api.persistence.sag.catalog_models import (
    CourseOfferRow,
    CourseRow,
    CurriculumRow,
    CurriculumSubjectRow,
    SubjectRow,
    TermRow,
    UnitRow,
)
from api.persistence.sag.class_models import ClassSectionRow, ProfessorRow, StudentClassRow
from api.persistence.sag.dialect import SagDialect
from api.persistence.sag.models import (
    EnrollmentHistoryRow,
    EnrollmentRow,
    PersonRow,
    TermEnrollmentRow,
)

SAG_OWNERSHIP: OwnershipMap = {
    PersonRow: lambda session: PersonRow.id.in_(session.person_ids),
    EnrollmentRow: lambda session: EnrollmentRow.person_id.in_(session.person_ids),
    EnrollmentHistoryRow: lambda session: tuple_(
        EnrollmentHistoryRow.brand, EnrollmentHistoryRow.student_id
    ).in_(SagDialect.source_keys(session.enrollment_keys)),
    TermEnrollmentRow: lambda session: tuple_(
        TermEnrollmentRow.brand, TermEnrollmentRow.student_id
    ).in_(SagDialect.source_keys(session.enrollment_keys)),
    StudentClassRow: lambda session: tuple_(StudentClassRow.brand, StudentClassRow.student_id).in_(
        SagDialect.source_keys(session.enrollment_keys)
    ),
    UnitRow: lambda session: UnitRow.brand.in_(SagDialect.source_brands(session.brands)),
    CourseOfferRow: lambda _: CourseOfferRow.unit_id.in_(select(UnitRow.id)),
    ClassSectionRow: lambda session: ClassSectionRow.brand.in_(
        SagDialect.source_brands(session.brands)
    ),
    ProfessorRow: lambda session: ProfessorRow.brand.in_(SagDialect.source_brands(session.brands)),
    TermRow: PUBLIC,
    CourseRow: PUBLIC,
    CurriculumRow: PUBLIC,
    CurriculumSubjectRow: PUBLIC,
    SubjectRow: PUBLIC,
}
