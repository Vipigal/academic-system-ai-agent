from collections.abc import Collection

from sqlalchemy import ColumnElement, func, tuple_

from api.domain.shared.brand import Brand, EnrollmentRef, Modality
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
    @staticmethod
    def tenants_of(brands: Collection[Brand]) -> list[str]:
        return [tenant for brand, tenant in TENANT_BY_BRAND.items() if brand in brands]

    @classmethod
    def account_of(cls, enrollments: Collection[EnrollmentRef]) -> ColumnElement[bool]:
        keys = [cls.account_key(enrollment) for enrollment in enrollments]
        return tuple_(LmsUserRow.tenant_id, cls._student_key()).in_(keys)

    @staticmethod
    def account_key(enrollment: EnrollmentRef) -> tuple[str, str]:
        tenant = TENANT_BY_BRAND[enrollment.brand]
        prefix = STUDENT_PREFIX_BY_MODALITY[enrollment.modality]
        return tenant, f"{prefix}_{enrollment.student_number}"

    @staticmethod
    def user_key(user: LmsUserRow) -> tuple[str, str]:
        return user.tenant_id, (user.student_id or "").strip().upper()

    @staticmethod
    def _student_key() -> ColumnElement[str]:
        return func.upper(func.trim(LmsUserRow.student_id))
