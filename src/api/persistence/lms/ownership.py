from api.persistence.core.base import Base
from api.persistence.core.ownership import OwnershipRule, Via
from api.persistence.lms.dialect import LmsDialect
from api.persistence.lms.models import (
    LmsCourseModuleRow,
    LmsCourseRow,
    LmsEnrolmentRow,
    LmsLogRow,
    LmsQuizAttemptRow,
    LmsQuizRow,
    LmsUserRow,
)

LMS_OWNERSHIP: dict[type[Base], OwnershipRule] = {
    LmsUserRow: lambda session: LmsDialect.account_of(session.enrollments),
    LmsEnrolmentRow: Via(LmsUserRow, LmsEnrolmentRow.user_id == LmsUserRow.id),
    LmsQuizAttemptRow: Via(LmsUserRow, LmsQuizAttemptRow.user_id == LmsUserRow.id),
    LmsLogRow: Via(LmsUserRow, LmsLogRow.user_id == LmsUserRow.id),
    LmsCourseRow: lambda session: LmsCourseRow.tenant_id.in_(LmsDialect.tenants_of(session.brands)),
    LmsQuizRow: Via(LmsCourseRow, LmsQuizRow.course_id == LmsCourseRow.id),
    LmsCourseModuleRow: Via(LmsCourseRow, LmsCourseModuleRow.course_id == LmsCourseRow.id),
}
