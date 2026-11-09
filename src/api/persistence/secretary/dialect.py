from collections.abc import Collection, Mapping

from sqlalchemy import ColumnElement, Select, and_, func, or_, select, tuple_

from api.domain.identity.session import EnrollmentKey
from api.domain.shared.brand import Brand, EnrollmentRef, Modality
from api.persistence.core.source_enum import UnknownDialectValueError
from api.persistence.identity.tables import PROTOCOL_REQUESTER
from api.persistence.sag.models import EnrollmentRow

UNIT_PREFIX_BY_BRAND = {
    Brand.SAO_PAULO: "SPA",
    Brand.MONTANHAS: "MON",
    Brand.LITORAL: "LIT",
    Brand.ATLANTICO: "ATL",
    Brand.ARAUCARIA: "ARA",
}
UNIT_CODE_BY_ACADEMIC_UNIT = {
    "CAMPUS PAULISTA": "SPA-PAU",
    "CAMPUS CAMPINAS": "SPA-CPS",
    "POLO SAO PAULO - PAULISTA": "SPA-SAO-EAD",
    "POLO CAMPINAS CENTRO": "SPA-CPS-EAD",
    "POLO RIBEIRAO PRETO": "SPA-RAO-EAD",
    "POLO SANTOS - GONZAGA": "SPA-STS-EAD",
    "POLO RIO DE JANEIRO - CENTRO": "SPA-RIO-EAD",
    "CAMPUS SAVASSI": "MON-SAV",
    "CAMPUS UBERLANDIA": "MON-UDI",
    "POLO BELO HORIZONTE - CENTRO": "MON-BHZ-EAD",
    "POLO JUIZ DE FORA": "MON-JDF-EAD",
    "POLO GOIANIA - SETOR BUENO": "MON-GYN-EAD",
    "CAMPUS BOTAFOGO": "LIT-BOT",
    "CAMPUS NITEROI": "LIT-NIT",
    "POLO RIO DE JANEIRO - TIJUCA": "LIT-RIO-EAD",
    "POLO VITORIA": "LIT-VIX-EAD",
    "CAMPUS PITUBA": "ATL-PIT",
    "CAMPUS RECIFE - BOA VISTA": "ATL-REC",
    "POLO SALVADOR - IGUATEMI": "ATL-SSA-EAD",
    "POLO RECIFE": "ATL-REC-EAD",
    "POLO FORTALEZA - ALDEOTA": "ATL-FOR-EAD",
    "POLO SAO PAULO - MOOCA": "ATL-SAO-EAD",
    "CAMPUS BATEL": "ARA-BAT",
    "CAMPUS PORTO ALEGRE": "ARA-POA",
    "POLO CURITIBA - CENTRO": "ARA-CWB-EAD",
    "POLO JOINVILLE": "ARA-JOI-EAD",
    "POLO PORTO ALEGRE - MOINHOS": "ARA-POA-EAD",
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
    @staticmethod
    def unit_code(academic_unit_name: str) -> str:
        unit_code = UNIT_CODE_BY_ACADEMIC_UNIT.get(academic_unit_name)
        if unit_code is None:
            raise UnknownDialectValueError(academic_unit_name)
        return unit_code

    @classmethod
    def protocols_of(cls, cpf: str, keys: Collection[EnrollmentKey]) -> Select[str]:
        student_ids = {key.ref: key.student_id for key in keys}
        requested = REQUESTER.outerjoin(OTHER_ENROLLMENT, NAMED_ENROLLMENT)
        return (
            select(REQUESTER.c.protocol)
            .select_from(requested)
            .where(cls._owned_by(cpf, student_ids))
        )

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
