from collections.abc import Collection

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.domain.session import StudentSession
from api.persistence.identity_queries import IdentityQueries
from api.persistence.sag.dialect import SagDialect


class StudentSessionRepository:
    def __init__(self, db_session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._db_session_factory = db_session_factory

    async def load(self, person_id: str) -> StudentSession:
        async with self._db_session_factory() as db:
            cpf = await self._cpf_of(db, person_id)
            if not cpf:
                return self._empty_session()
            person_ids = await self._values(db, IdentityQueries.person_ids_of(cpf))
            enrollment_keys = await self._enrollment_keys_of(db, person_ids)
            return await self._session_of(db, cpf, person_ids, enrollment_keys)

    @staticmethod
    def _empty_session() -> StudentSession:
        return StudentSession(
            person_ids=frozenset(),
            cpf="",
            enrollment_keys=frozenset(),
            brands=frozenset(),
            contract_ids=frozenset(),
            self_paid_contract_ids=frozenset(),
            lms_user_ids=frozenset(),
            protocol_ids=frozenset(),
        )

    @classmethod
    async def _session_of(
        cls,
        db: AsyncSession,
        cpf: str,
        person_ids: frozenset[str],
        enrollment_keys: frozenset[tuple[str, str]],
    ) -> StudentSession:
        student_ids = {SagDialect.enrollment_ref(*key): key[1] for key in enrollment_keys}
        contract_ids = await cls._values(db, IdentityQueries.contracts_of(student_ids))
        return StudentSession(
            person_ids=person_ids,
            cpf=cpf,
            enrollment_keys=enrollment_keys,
            brands=frozenset(enrollment.brand for enrollment in student_ids),
            contract_ids=contract_ids,
            self_paid_contract_ids=await cls._values(
                db, IdentityQueries.self_paid_of(cpf, contract_ids)
            ),
            lms_user_ids=await cls._values(db, IdentityQueries.lms_accounts_of(student_ids)),
            protocol_ids=await cls._values(db, IdentityQueries.protocols_of(cpf, student_ids)),
        )

    @staticmethod
    async def _cpf_of(db: AsyncSession, person_id: str) -> str:
        result = await db.scalars(IdentityQueries.cpf_of(person_id))
        return SagDialect.normalized_cpf(result.one_or_none() or "")

    @staticmethod
    async def _enrollment_keys_of(
        db: AsyncSession, person_ids: Collection[str]
    ) -> frozenset[tuple[str, str]]:
        result = await db.scalars(IdentityQueries.enrollments_of(person_ids))
        return frozenset((row.brand, row.student_id) for row in result.all())

    @staticmethod
    async def _values(db: AsyncSession, statement: Select[str]) -> frozenset[str]:
        result = await db.scalars(statement)
        return frozenset(result.all())
