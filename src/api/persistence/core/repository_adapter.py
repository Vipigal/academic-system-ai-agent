from collections.abc import Sequence

from sqlalchemy import FromClause, Select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.base import Executable

from api.domain.identity.session import StudentSession
from api.persistence.core.base import Base
from api.persistence.core.ownership import (
    DeclaredQuery,
    DeclaredRows,
    Public,
    Update,
    Via,
)
from api.persistence.core.ownership_registry import OwnershipRegistry
from api.persistence.core.query_guard import QueryGuard
from api.persistence.core.write_plan import WritePlan


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
        QueryGuard.reject_unsafe_constructs(stmt)
        guarded = self._with_ownership(stmt)
        async with self._db_session_factory() as db:
            result = await db.scalars(guarded)
            return result.all()

    async def fetch_declared[*RowT](self, query: DeclaredQuery[*RowT]) -> DeclaredRows[*RowT]:
        OwnershipRegistry.assert_declared(query)
        stmt = query.build(self._student_session)
        query.assert_rooted(QueryGuard.tables_in(stmt))
        guarded = self._with_ownership(stmt)
        async with self._db_session_factory() as db:
            result = await db.execute(guarded)
            return result.all()

    async def write(self, *steps: Sequence[Base] | Update) -> None:
        prepared = [WritePlan.prepare(step, self._student_session) for step in steps]
        async with self._db_session_factory() as db, db.begin():
            for step in prepared:
                if isinstance(step, Executable):
                    await db.execute(step)
                else:
                    db.add_all(step)
                    await db.flush()

    def _with_ownership[*RowT](self, stmt: Select[*RowT]) -> Select[*RowT]:
        tables = QueryGuard.tables_in(stmt)
        for table in tables:
            stmt = self._apply_rule(stmt, table, tables)
        return stmt

    def _apply_rule[*RowT](
        self, stmt: Select[*RowT], table: FromClause, tables: list[FromClause]
    ) -> Select[*RowT]:
        rule = OwnershipRegistry.rule_of(table)
        if isinstance(rule, Public):
            return stmt
        if isinstance(rule, Via):
            rule.assert_joined(table, tables)
            return stmt.where(rule.link)
        return stmt.where(rule(self._student_session))
