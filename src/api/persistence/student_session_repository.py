from collections.abc import Collection

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.domain.brand import EnrollmentRef
from api.domain.session import StudentSession
from api.persistence.finance.dialect import FinanceDialect
from api.persistence.finance.models import ContractRow
from api.persistence.sag.dialect import SagDialect
from api.persistence.sag.models import EnrollmentRow, PersonRow


class StudentSessionRepository:
    def __init__(self, db_session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._db_session_factory = db_session_factory

    async def load(self, person_id: str) -> StudentSession:
        async with self._db_session_factory() as db:
            person_ids = await self._person_ids_of(db, person_id)
            enrollments = await self._enrollments_of(db, person_ids)
            contract_ids = await self._contracts_of(db, enrollments)
        return StudentSession(person_ids=person_ids, contract_ids=contract_ids)

    @staticmethod
    async def _person_ids_of(db: AsyncSession, person_id: str) -> frozenset[str]:
        same_cpf = select(PersonRow.cpf).where(PersonRow.id == person_id).scalar_subquery()
        statement = select(PersonRow.id).where(PersonRow.cpf == same_cpf)
        result = await db.scalars(statement)
        return frozenset(result.all())

    @staticmethod
    async def _enrollments_of(
        db: AsyncSession, person_ids: Collection[str]
    ) -> frozenset[EnrollmentRef]:
        result = await db.scalars(
            select(EnrollmentRow).where(EnrollmentRow.person_id.in_(person_ids))
        )
        return frozenset(
            SagDialect.enrollment_ref(row.brand, row.student_id) for row in result.all()
        )

    @staticmethod
    async def _contracts_of(
        db: AsyncSession, enrollments: Collection[EnrollmentRef]
    ) -> frozenset[str]:
        result = await db.scalars(
            select(ContractRow.id).where(FinanceDialect.contract_of(enrollments))
        )
        return frozenset(result.all())
