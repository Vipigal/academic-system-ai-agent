from api.persistence.base import Base
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
from api.persistence.ownership import OwnershipRule, Via

LMS_OWNERSHIP: dict[type[Base], OwnershipRule] = {
    LmsUserRow: lambda session: LmsUserRow.id.in_(session.lms_user_ids),
    LmsEnrolmentRow: lambda session: LmsEnrolmentRow.user_id.in_(session.lms_user_ids),
    LmsQuizAttemptRow: lambda session: LmsQuizAttemptRow.user_id.in_(session.lms_user_ids),
    LmsLogRow: lambda session: LmsLogRow.user_id.in_(session.lms_user_ids),
    LmsCourseRow: lambda session: LmsCourseRow.tenant_id.in_(LmsDialect.tenants_of(session.brands)),
    LmsQuizRow: Via(LmsCourseRow, LmsQuizRow.course_id == LmsCourseRow.id),
    LmsCourseModuleRow: Via(LmsCourseRow, LmsCourseModuleRow.course_id == LmsCourseRow.id),
}
