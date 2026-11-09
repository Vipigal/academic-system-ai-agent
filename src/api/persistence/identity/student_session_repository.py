from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.identity.dev_student import DevStudent
from api.domain.identity.session import StudentSession
from api.persistence.core.database import Database
from api.persistence.core.ownership_criteria import SKIP_OWNERSHIP
from api.persistence.identity.queries import IdentityQueries
from api.persistence.sag.dialect import SagDialect

type IdentityRow = tuple[str, str, str]

BEFORE_THE_STUDENT = {SKIP_OWNERSHIP: True}


class StudentSessionRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def load(self, person_id: str) -> StudentSession:
        async with self._database.db_session_factory() as db:
            cpf = await self._cpf_of(db, person_id)
            if not cpf:
                return self._empty_session()
            identities = IdentityQueries.identities_of(cpf)
            result = await db.execute(identities, execution_options=BEFORE_THE_STUDENT)
            return self._session_of(cpf, result.all())

    async def person_of(self, brand: str, student_id: str) -> str | None:
        async with self._database.db_session_factory() as db:
            person = IdentityQueries.person_of(brand, student_id)
            result = await db.scalars(person, execution_options=BEFORE_THE_STUDENT)
            return result.one_or_none()

    async def dev_students(self) -> Sequence[DevStudent]:
        async with self._database.db_session_factory() as db:
            students = IdentityQueries.dev_students()
            result = await db.execute(students, execution_options=BEFORE_THE_STUDENT)
            return [DevStudent(*row) for row in result.all()]

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
        cpf_query = IdentityQueries.cpf_of(person_id)
        result = await db.scalars(cpf_query, execution_options=BEFORE_THE_STUDENT)
        return SagDialect.normalized_cpf(result.one_or_none() or "")
