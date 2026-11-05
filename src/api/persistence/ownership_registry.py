from sqlalchemy import FromClause, MetaData

from api.persistence.base import Base
from api.persistence.finance.ownership import FINANCE_OWNERSHIP
from api.persistence.lms.ownership import LMS_OWNERSHIP
from api.persistence.ownership import OwnershipError, OwnershipRule
from api.persistence.sag.ownership import SAG_OWNERSHIP
from api.persistence.secretary.ownership import SECRETARY_OWNERSHIP

OWNERSHIP_BY_SYSTEM = (FINANCE_OWNERSHIP, LMS_OWNERSHIP, SAG_OWNERSHIP, SECRETARY_OWNERSHIP)
OWNERSHIP_BY_TABLE: dict[FromClause, OwnershipRule] = {
    row.__table__: rule for system in OWNERSHIP_BY_SYSTEM for row, rule in system.items()
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
