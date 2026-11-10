from collections.abc import Sequence

from sqlalchemy import Select, Update
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.identity.session import StudentSession
from api.persistence.core.base import Base
from api.persistence.core.database import Database
from api.persistence.core.ownership_criteria import STUDENT, OwnershipRegistry

type Rows[*RowT] = Sequence[tuple[*RowT]]


class RepositoryAdapter:
    def __init__(self, database: Database, student_session: StudentSession) -> None:
        self._database = database
        self._student_session = student_session

    @property
    def student_session(self) -> StudentSession:
        return self._student_session

    async def fetch[RowT](self, stmt: Select[RowT]) -> Sequence[RowT]:
        async with self._db_session() as db:
            result = await db.scalars(stmt)
            return result.all()

    async def fetch_rows[*RowT](self, stmt: Select[*RowT]) -> Rows[*RowT]:
        async with self._db_session() as db:
            result = await db.execute(stmt)
            return result.all()

    async def write(self, *steps: Sequence[Base] | Update) -> None:
        for step in steps:
            self._assert_declared(step)
        async with self._db_session() as db, db.begin():
            for step in steps:
                if isinstance(step, Update):
                    await db.execute(step)
                else:
                    db.add_all(step)
                    await db.flush()

    def _db_session(self) -> AsyncSession:
        return self._database.db_session_factory(info={STUDENT: self._student_session})

    @staticmethod
    def _assert_declared(step: Sequence[Base] | Update) -> None:
        if not isinstance(step, Update):
            for row in step:
                OwnershipRegistry.rule_of(row.__table__)
