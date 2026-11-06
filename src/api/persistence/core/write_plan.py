from collections.abc import Sequence

from sqlalchemy import update
from sqlalchemy.sql.base import Executable

from api.domain.identity.session import StudentSession
from api.persistence.core.base import Base
from api.persistence.core.ownership import OwnershipError, Public, Update, Via
from api.persistence.core.ownership_registry import OwnershipRegistry


class WritePlan:
    @classmethod
    def prepare(
        cls, step: Sequence[Base] | Update, session: StudentSession
    ) -> Sequence[Base] | Executable:
        if isinstance(step, Update):
            return cls._owned_update(step, session)
        for row in step:
            OwnershipRegistry.rule_of(row.__table__)
        return step

    @staticmethod
    def _owned_update(step: Update, session: StudentSession) -> Executable:
        rule = OwnershipRegistry.rule_of(step.row.__table__)
        if isinstance(rule, Via | Public):
            message = "update exige dono por predicado"
            raise OwnershipError(message)
        statement = update(step.row).where(step.where, rule(session))
        return statement.values(step.values)
