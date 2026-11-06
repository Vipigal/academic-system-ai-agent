from collections.abc import Collection, Mapping

from sqlalchemy import ColumnElement, Select, and_, func, or_, select, tuple_

from api.domain.identity.session import EnrollmentKey
from api.domain.shared.brand import Brand, EnrollmentRef, Modality
from api.persistence.identity.tables import PROTOCOL_REQUESTER
from api.persistence.sag.models import EnrollmentRow

UNIT_PREFIX_BY_BRAND = {
    Brand.SAO_PAULO: "SPA",
    Brand.MONTANHAS: "MON",
    Brand.LITORAL: "LIT",
    Brand.ATLANTICO: "ATL",
    Brand.ARAUCARIA: "ARA",
}
GUARDIAN = "Guardian"
STUDENT_REQUESTERS = ("Student", "Alumni")
STUDENT_ID_LENGTH = 6
CPF_LENGTH = 11
REQUESTER = PROTOCOL_REQUESTER.alias("requester")
UNIT_PREFIX = func.split_part(REQUESTER.c.unit_code, "-", 1)
ONLINE_UNIT = REQUESTER.c.unit_code.endswith("-EAD")
STUDENT_ID = func.lpad(REQUESTER.c.stu_id, STUDENT_ID_LENGTH, "0")
ASKED_BY_STUDENT = REQUESTER.c.requester_type.in_(STUDENT_REQUESTERS)
ASKED_BY_GUARDIAN = REQUESTER.c.requester_type == GUARDIAN
OTHER_ENROLLMENT = EnrollmentRow.__table__.alias("other_enrollment")
NAMED_ENROLLMENT = OTHER_ENROLLMENT.c.student_id == STUDENT_ID
ID_OF_NO_ENROLLMENT = OTHER_ENROLLMENT.c.student_id.is_(None)


class SecretaryDialect:
    @classmethod
    def protocols_of(cls, cpf: str, keys: Collection[EnrollmentKey]) -> Select[str]:
        student_ids = {key.ref: key.student_id for key in keys}
        requested = select(REQUESTER.c.protocol).outerjoin(OTHER_ENROLLMENT, NAMED_ENROLLMENT)
        return requested.where(cls._owned_by(cpf, student_ids))

    @classmethod
    def _owned_by(cls, cpf: str, student_ids: Mapping[EnrollmentRef, str]) -> ColumnElement[bool]:
        asked_by_the_person = cls._asked_by_student_with(cpf)
        return or_(
            and_(cls._names_own_enrollment(student_ids), asked_by_the_person),
            and_(cls._names_own_enrollment(student_ids), ASKED_BY_GUARDIAN),
            and_(asked_by_the_person, cls._opened_in_own_unit(student_ids), ID_OF_NO_ENROLLMENT),
        )

    @classmethod
    def _names_own_enrollment(cls, student_ids: Mapping[EnrollmentRef, str]) -> ColumnElement[bool]:
        keys = [
            (*cls._unit_key(enrollment), student_id)
            for enrollment, student_id in student_ids.items()
        ]
        return tuple_(UNIT_PREFIX, ONLINE_UNIT, STUDENT_ID).in_(keys)

    @classmethod
    def _opened_in_own_unit(cls, student_ids: Mapping[EnrollmentRef, str]) -> ColumnElement[bool]:
        keys = [cls._unit_key(enrollment) for enrollment in student_ids]
        return tuple_(UNIT_PREFIX, ONLINE_UNIT).in_(keys)

    @staticmethod
    def _asked_by_student_with(cpf: str) -> ColumnElement[bool]:
        requester_cpf = func.lpad(REQUESTER.c.requester_cpf, CPF_LENGTH, "0")
        return and_(ASKED_BY_STUDENT, requester_cpf == cpf)

    @staticmethod
    def _unit_key(enrollment: EnrollmentRef) -> tuple[str, bool]:
        return UNIT_PREFIX_BY_BRAND[enrollment.brand], enrollment.modality is Modality.ONLINE
