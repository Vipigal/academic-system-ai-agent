import pytest
from sqlalchemy import Table, select

from api.domain.session import StudentSession
from api.persistence.database import Database
from api.persistence.identity_tables import IDENTITY_METADATA
from api.persistence.lms.models import LmsUserRow
from api.persistence.ownership import OwnershipError
from api.persistence.repository_adapter import RepositoryAdapter
from api.persistence.secretary.models import ProtocolRow
from api.persistence.student_session_repository import StudentSessionRepository

PERSON_WITH_ACCOUNT_AND_PROTOCOLS = "3000071"


async def session_of(database: Database, person_id: str) -> StudentSession:
    return await StudentSessionRepository(database.db_session_factory).load(person_id)


async def adapter_of(database: Database, person_id: str) -> RepositoryAdapter:
    session = await session_of(database, person_id)
    return RepositoryAdapter(database.db_session_factory, session)


async def test_adapter_limits_lms_accounts_to_the_session(database: Database) -> None:
    session = await session_of(database, PERSON_WITH_ACCOUNT_AND_PROTOCOLS)
    adapter = RepositoryAdapter(database.db_session_factory, session)
    accounts = await adapter.fetch(select(LmsUserRow))
    assert session.lms_user_ids
    assert {row.id for row in accounts} == session.lms_user_ids


async def test_adapter_limits_protocols_to_the_session(database: Database) -> None:
    session = await session_of(database, PERSON_WITH_ACCOUNT_AND_PROTOCOLS)
    adapter = RepositoryAdapter(database.db_session_factory, session)
    protocols = await adapter.fetch(select(ProtocolRow))
    assert session.protocol_ids
    assert {row.id for row in protocols} == session.protocol_ids


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
