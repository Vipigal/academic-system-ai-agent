from collections.abc import Collection, Mapping

from sqlalchemy import Select, select

from api.domain.brand import EnrollmentRef
from api.persistence.finance.dialect import FinanceDialect
from api.persistence.finance.models import ContractRow
from api.persistence.identity_tables import (
    PERSON_CPF,
    PROTOCOL_REQUESTER,
)
from api.persistence.lms.dialect import LmsDialect
from api.persistence.lms.models import LmsUserRow
from api.persistence.sag.dialect import SagDialect
from api.persistence.sag.models import EnrollmentRow
from api.persistence.secretary.dialect import SecretaryDialect


class IdentityQueries:
    @staticmethod
    def cpf_of(person_id: str) -> Select[str]:
        return select(PERSON_CPF.c.cpf).where(PERSON_CPF.c.person_id == person_id)

    @staticmethod
    def person_ids_of(cpf: str) -> Select[str]:
        return select(PERSON_CPF.c.person_id).where(SagDialect.person_with_cpf(cpf))

    @staticmethod
    def enrollments_of(person_ids: Collection[str]) -> Select[EnrollmentRow]:
        return select(EnrollmentRow).where(EnrollmentRow.person_id.in_(person_ids))

    @staticmethod
    def contracts_of(enrollments: Collection[EnrollmentRef]) -> Select[str]:
        return select(ContractRow.id).where(FinanceDialect.contract_of(enrollments))

    @staticmethod
    def lms_accounts_of(enrollments: Collection[EnrollmentRef]) -> Select[str]:
        return select(LmsUserRow.id).where(LmsDialect.account_of(enrollments))

    @staticmethod
    def protocols_of(cpf: str, student_ids: Mapping[EnrollmentRef, str]) -> Select[str]:
        ownership = SecretaryDialect.protocol_of(cpf, student_ids)
        return select(PROTOCOL_REQUESTER.c.protocol).where(ownership)
