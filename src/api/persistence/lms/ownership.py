from sqlalchemy import select

from api.persistence.core.ownership import OwnershipMap
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

LMS_OWNERSHIP: OwnershipMap = {
    LmsUserRow: lambda session: LmsDialect.account_of(session.enrollments),
    LmsEnrolmentRow: lambda _: LmsEnrolmentRow.user_id.in_(select(LmsUserRow.id)),
    LmsQuizAttemptRow: lambda _: LmsQuizAttemptRow.user_id.in_(select(LmsUserRow.id)),
    LmsLogRow: lambda _: LmsLogRow.user_id.in_(select(LmsUserRow.id)),
    LmsCourseRow: lambda session: LmsCourseRow.tenant_id.in_(LmsDialect.tenants_of(session.brands)),
    LmsQuizRow: lambda _: LmsQuizRow.course_id.in_(select(LmsCourseRow.id)),
    LmsCourseModuleRow: lambda _: LmsCourseModuleRow.course_id.in_(select(LmsCourseRow.id)),
}
