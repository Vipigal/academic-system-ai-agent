from collections.abc import Sequence

from sqlalchemy import FromClause, Select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.domain.session import StudentSession
from api.persistence.ownership import Public, Via
from api.persistence.ownership_registry import OwnershipRegistry
from api.persistence.query_guard import QueryGuard


class RepositoryAdapter:
    def __init__(
        self,
        db_session_factory: async_sessionmaker[AsyncSession],
        student_session: StudentSession,
    ) -> None:
        self._db_session_factory = db_session_factory
        self._student_session = student_session

    @property
    def student_session(self) -> StudentSession:
        return self._student_session

    async def fetch[RowT](self, stmt: Select[RowT]) -> Sequence[RowT]:
        guarded = self._with_ownership(stmt)
        async with self._db_session_factory() as db:
            result = await db.scalars(guarded)
            return result.all()

    def _with_ownership[RowT](self, stmt: Select[RowT]) -> Select[RowT]:
        QueryGuard.reject_unsafe_constructs(stmt)
        tables = QueryGuard.tables_in(stmt)
        for table in tables:
            stmt = self._apply_rule(stmt, table, tables)
        return stmt

    def _apply_rule[RowT](
        self, stmt: Select[RowT], table: FromClause, tables: list[FromClause]
    ) -> Select[RowT]:
        rule = OwnershipRegistry.rule_of(table)
        if isinstance(rule, Public):
            return stmt
        if isinstance(rule, Via):
            rule.assert_joined(table, tables)
            return stmt.where(rule.link)
        return stmt.where(rule(self._student_session))
