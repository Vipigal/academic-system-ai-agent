from sqlalchemy import Select, select

from api.persistence.identity.tables import PERSON_CPF
from api.persistence.sag.models import PersonRow

REQUESTER = PERSON_CPF.alias("requester")


class RequesterQueries:
    @staticmethod
    def names_of_the_session() -> Select[str, str]:
        name = (
            select(REQUESTER.c.full_name)
            .where(REQUESTER.c.person_id == PersonRow.id)
            .scalar_subquery()
        )
        return select(PersonRow.id, name)
