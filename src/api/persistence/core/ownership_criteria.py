from sqlalchemy import FromClause, MetaData
from sqlalchemy.orm import ORMExecuteState, with_loader_criteria
from sqlalchemy.orm.interfaces import ORMOption

from api.domain.identity.session import StudentSession
from api.persistence.agent.ownership import AGENT_OWNERSHIP
from api.persistence.core.base import Base
from api.persistence.core.ownership import OwnershipError, OwnershipMap, OwnershipRule
from api.persistence.finance.ownership import FINANCE_OWNERSHIP
from api.persistence.lms.ownership import LMS_OWNERSHIP
from api.persistence.sag.ownership import SAG_OWNERSHIP
from api.persistence.secretary.ownership import SECRETARY_OWNERSHIP

STUDENT = "student"
SKIP_OWNERSHIP = "skip_ownership"
OWNERSHIP_BY_SYSTEM = (
    AGENT_OWNERSHIP,
    FINANCE_OWNERSHIP,
    LMS_OWNERSHIP,
    SAG_OWNERSHIP,
    SECRETARY_OWNERSHIP,
)
OWNERSHIP_BY_ROW: OwnershipMap = {
    row: rule for system in OWNERSHIP_BY_SYSTEM for row, rule in system.items()
}
OWNERSHIP_BY_TABLE: dict[FromClause, OwnershipRule] = {
    row.__table__: rule for row, rule in OWNERSHIP_BY_ROW.items()
}


class OwnershipRegistry:
    @staticmethod
    def rule_of(table: FromClause) -> OwnershipRule:
        if table not in OWNERSHIP_BY_TABLE:
            message = f"tabela sem declaração de ownership: {table}"
            raise OwnershipError(message)
        return OWNERSHIP_BY_TABLE[table]

    @staticmethod
    def assert_complete(metadata: MetaData = Base.metadata) -> None:
        undeclared = [
            table.fullname for table in metadata.tables.values() if table not in OWNERSHIP_BY_TABLE
        ]
        if undeclared:
            message = f"tabelas sem declaração de ownership: {undeclared}"
            raise OwnershipError(message)


class OwnershipCriteria:
    @classmethod
    def apply(cls, state: ORMExecuteState) -> None:
        if not cls._is_guarded(state):
            return
        student = cls._student_of(state)
        cls._assert_declared(state)
        state.statement = state.statement.options(*cls._criteria_of(student))

    @staticmethod
    def _is_guarded(state: ORMExecuteState) -> bool:
        reads_or_changes = state.is_select or state.is_update or state.is_delete
        return reads_or_changes and not state.execution_options.get(SKIP_OWNERSHIP, False)

    @staticmethod
    def _student_of(state: ORMExecuteState) -> StudentSession:
        student = state.session.info.get(STUDENT)
        if not isinstance(student, StudentSession):
            message = "sessão de banco sem aluno"
            raise OwnershipError(message)
        return student

    @staticmethod
    def _assert_declared(state: ORMExecuteState) -> None:
        if not state.is_orm_statement:
            message = "consulta sem model com declaração de ownership"
            raise OwnershipError(message)
        for mapper in state.all_mappers:
            OwnershipRegistry.rule_of(mapper.local_table)

    @staticmethod
    def _criteria_of(student: StudentSession) -> list[ORMOption]:
        return [
            with_loader_criteria(row, rule(student), include_aliases=True)
            for row, rule in OWNERSHIP_BY_ROW.items()
            if rule is not None
        ]
