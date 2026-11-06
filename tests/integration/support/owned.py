from dataclasses import dataclass

from sqlalchemy import select

from api.domain.finance.contract import PayerType
from api.domain.identity.session import StudentSession
from api.persistence.core.database import Database
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.finance.repositories import SqlFinanceRepository
from api.persistence.lms.models import LmsUserRow
from api.persistence.secretary.models import ProtocolRow


@dataclass(frozen=True, slots=True)
class Owned:
    session: StudentSession
    contract_ids: frozenset[str]
    self_paid_contract_ids: frozenset[str]
    lms_user_ids: frozenset[str]
    protocol_ids: frozenset[str]

    @property
    def person_ids(self) -> frozenset[str]:
        return self.session.person_ids

    @property
    def cpf(self) -> str:
        return self.session.cpf

    @property
    def enrollment_keys(self) -> frozenset[tuple[str, str]]:
        return frozenset((key.source_brand, key.student_id) for key in self.session.enrollment_keys)


async def owned_by(database: Database, session: StudentSession) -> Owned:
    adapter = RepositoryAdapter(database.db_session_factory, session)
    contracts = await SqlFinanceRepository(adapter).list_contracts()
    return Owned(
        session=session,
        contract_ids=frozenset(contract.id for contract in contracts),
        self_paid_contract_ids=frozenset(
            contract.id for contract in contracts if contract.payer is PayerType.SELF
        ),
        lms_user_ids=frozenset(await adapter.fetch(select(LmsUserRow.id))),
        protocol_ids=frozenset(await adapter.fetch(select(ProtocolRow.id))),
    )
