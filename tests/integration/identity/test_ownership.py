import pytest
from sqlalchemy import Table, select

from api.domain.identity.session import StudentSession
from api.persistence.core.database import Database
from api.persistence.core.ownership import OwnershipError
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.identity.student_session_repository import StudentSessionRepository
from api.persistence.identity.tables import IDENTITY_METADATA
from api.persistence.lms.models import LmsUserRow
from api.persistence.secretary.models import ProtocolRow
from tests.integration.support.sql_oracle import LMS_OWNERS, PROTOCOL_OWNERS, SqlOracle

PERSON_WITH_ACCOUNT_AND_PROTOCOLS = "3000071"


async def session_of(database: Database, person_id: str) -> StudentSession:
    return await StudentSessionRepository(database).load(person_id)


async def adapter_of(database: Database, person_id: str) -> RepositoryAdapter:
    session = await session_of(database, person_id)
    return RepositoryAdapter(database, session)


async def test_adapter_limits_lms_accounts_to_the_session(database: Database) -> None:
    session = await session_of(database, PERSON_WITH_ACCOUNT_AND_PROTOCOLS)
    adapter = RepositoryAdapter(database, session)
    accounts = await adapter.fetch(select(LmsUserRow))
    expected = await SqlOracle().owned_by_cpf(LMS_OWNERS, session.cpf)
    assert expected
    assert {row.id for row in accounts} == expected


async def test_adapter_limits_protocols_to_the_session(database: Database) -> None:
    session = await session_of(database, PERSON_WITH_ACCOUNT_AND_PROTOCOLS)
    adapter = RepositoryAdapter(database, session)
    protocols = await adapter.fetch(select(ProtocolRow))
    expected = await SqlOracle().owned_by_cpf(PROTOCOL_OWNERS, session.cpf)
    assert expected
    assert {row.id for row in protocols} == expected


async def test_session_without_identity_sees_no_account_nor_protocol(database: Database) -> None:
    adapter = await adapter_of(database, "does-not-exist")
    assert await adapter.fetch(select(LmsUserRow)) == []
    assert await adapter.fetch(select(ProtocolRow)) == []


@pytest.mark.parametrize("table", IDENTITY_METADATA.tables.values(), ids=str)
async def test_adapter_refuses_the_private_identity_tables(
    database: Database, table: Table
) -> None:
    adapter = await adapter_of(database, PERSON_WITH_ACCOUNT_AND_PROTOCOLS)
    with pytest.raises(OwnershipError):
        await adapter.fetch(select(table))
