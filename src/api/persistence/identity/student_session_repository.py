from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.domain.identity.session import StudentSession
from api.persistence.identity.queries import IdentityQueries
from api.persistence.sag.dialect import SagDialect

type IdentityRow = tuple[str, str, str]


class StudentSessionRepository:
    def __init__(self, db_session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._db_session_factory = db_session_factory

    async def load(self, person_id: str) -> StudentSession:
        async with self._db_session_factory() as db:
            cpf = await self._cpf_of(db, person_id)
            if not cpf:
                return self._empty_session()
            result = await db.execute(IdentityQueries.identities_of(cpf))
            return self._session_of(cpf, result.all())

    async def person_of(self, brand: str, student_id: str) -> str | None:
        async with self._db_session_factory() as db:
            result = await db.scalars(IdentityQueries.person_of(brand, student_id))
            return result.one_or_none()

    async def full_name_of(self, person_id: str) -> str | None:
        async with self._db_session_factory() as db:
            result = await db.scalars(IdentityQueries.full_name_of(person_id))
            return result.one_or_none()

    @staticmethod
    def _empty_session() -> StudentSession:
        return StudentSession(person_ids=frozenset(), cpf="", enrollment_keys=frozenset())

    @staticmethod
    def _session_of(cpf: str, rows: Sequence[IdentityRow]) -> StudentSession:
        return StudentSession(
            person_ids=frozenset(person_id for person_id, _, _ in rows),
            cpf=cpf,
            enrollment_keys=frozenset(
                SagDialect.enrollment_key(brand, student_id)
                for _, brand, student_id in rows
                if brand and student_id
            ),
        )

    @staticmethod
    async def _cpf_of(db: AsyncSession, person_id: str) -> str:
        result = await db.scalars(IdentityQueries.cpf_of(person_id))
        return SagDialect.normalized_cpf(result.one_or_none() or "")
