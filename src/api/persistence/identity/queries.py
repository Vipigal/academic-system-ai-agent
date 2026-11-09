from sqlalchemy import Select, select

from api.persistence.identity.tables import PERSON_CPF
from api.persistence.sag.dialect import SagDialect
from api.persistence.sag.models import EnrollmentRow


class IdentityQueries:
    @staticmethod
    def cpf_of(person_id: str) -> Select[str]:
        return select(PERSON_CPF.c.cpf).where(PERSON_CPF.c.person_id == person_id)

    @staticmethod
    def identities_of(cpf: str) -> Select[str, str, str]:
        person = EnrollmentRow.person_id == PERSON_CPF.c.person_id
        return (
            select(PERSON_CPF.c.person_id, EnrollmentRow.brand, EnrollmentRow.student_id)
            .outerjoin(EnrollmentRow, person)
            .where(SagDialect.person_with_cpf(cpf))
        )

    @staticmethod
    def dev_students() -> Select[str, str, str, str]:
        return (
            select(
                EnrollmentRow.brand,
                EnrollmentRow.student_id,
                PERSON_CPF.c.full_name,
                EnrollmentRow.status,
            )
            .join(PERSON_CPF, EnrollmentRow.person_id == PERSON_CPF.c.person_id)
            .order_by(PERSON_CPF.c.full_name, EnrollmentRow.brand, EnrollmentRow.student_id)
        )

    @staticmethod
    def person_of(brand: str, student_id: str) -> Select[str]:
        return select(EnrollmentRow.person_id).where(
            EnrollmentRow.brand == brand, EnrollmentRow.student_id == student_id
        )
