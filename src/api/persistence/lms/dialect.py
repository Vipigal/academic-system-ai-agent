from collections.abc import Collection

from sqlalchemy import ColumnElement, func, tuple_

from api.domain.brand import Brand, EnrollmentRef, Modality
from api.persistence.lms.models import LmsUserRow

TENANT_BY_BRAND = {
    Brand.SAO_PAULO: "1",
    Brand.MONTANHAS: "2",
    Brand.LITORAL: "3",
    Brand.ATLANTICO: "4",
    Brand.ARAUCARIA: "5",
}
STUDENT_PREFIX_BY_MODALITY = {Modality.IN_PERSON: "PRES", Modality.ONLINE: "EAD"}


class LmsDialect:
    @classmethod
    def account_of(cls, enrollments: Collection[EnrollmentRef]) -> ColumnElement[bool]:
        keys = [cls._account_key(enrollment) for enrollment in enrollments]
        return tuple_(LmsUserRow.tenant_id, cls._student_key()).in_(keys)

    @staticmethod
    def _account_key(enrollment: EnrollmentRef) -> tuple[str, str]:
        tenant = TENANT_BY_BRAND[enrollment.brand]
        prefix = STUDENT_PREFIX_BY_MODALITY[enrollment.modality]
        return tenant, f"{prefix}_{enrollment.student_number}"

    @staticmethod
    def _student_key() -> ColumnElement[str]:
        return func.upper(func.trim(LmsUserRow.student_id))
