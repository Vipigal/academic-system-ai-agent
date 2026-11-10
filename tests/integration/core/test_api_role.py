import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from api.persistence.core.base import Base
from api.persistence.core.database import Database
from api.persistence.core.ownership_criteria import OwnershipRegistry
from api.persistence.identity.tables import IDENTITY_METADATA
from tests.integration.support.sql_oracle import SqlOracle

WRITABLE = {
    "secretary.protocol",
    "secretary.protocol_status_history",
    "secretary.protocol_interaction",
}
SOURCE_SCHEMAS = "('sag', 'lms', 'secretary', 'finance')"
GRANTED = """
    SELECT table_schema || '.' || table_name FROM information_schema.tables
    WHERE table_schema IN {schemas}
      AND has_table_privilege('api', table_schema || '.' || table_name, '{privilege}')
"""


def mapped_tables() -> set[str]:
    OwnershipRegistry.assert_complete()
    tables = set(Base.metadata.tables) | set(IDENTITY_METADATA.tables)
    return {table for table in tables if not table.startswith("agent.")}


async def test_the_role_reads_exactly_the_mapped_tables() -> None:
    query = GRANTED.format(schemas=SOURCE_SCHEMAS, privilege="SELECT")
    assert await SqlOracle().values(query) == mapped_tables()


async def test_the_role_writes_only_the_protocol_tables() -> None:
    query = GRANTED.format(schemas=SOURCE_SCHEMAS, privilege="INSERT")
    assert await SqlOracle().values(query) == WRITABLE


@pytest.mark.parametrize("privilege", ["UPDATE", "DELETE", "TRUNCATE"])
async def test_the_role_never_changes_source_data(privilege: str) -> None:
    assert (
        await SqlOracle().values(GRANTED.format(schemas=SOURCE_SCHEMAS, privilege=privilege))
        == set()
    )


async def test_the_role_is_not_a_superuser() -> None:
    assert await SqlOracle().values(
        "SELECT rolsuper::text FROM pg_roles WHERE rolname = 'api'"
    ) == {"false"}


async def test_the_api_connects_with_the_role(database: Database) -> None:
    async with database.db_session_factory() as db:
        assert await db.scalar(text("SELECT current_user")) == "api"


@pytest.mark.parametrize(
    "statement",
    [
        pytest.param("SELECT * FROM secretary.analyst", id="read-analyst"),
        pytest.param("UPDATE finance.invoice SET contractid = contractid", id="update-source"),
        pytest.param("DELETE FROM secretary.protocol", id="delete-source"),
        pytest.param("CREATE TEMP TABLE scratch (id text)", id="temp-table"),
        pytest.param("CREATE TABLE agent.scratch (id text)", id="create-table"),
    ],
)
async def test_the_role_is_denied(database: Database, statement: str) -> None:
    async with database.db_session_factory() as db:
        with pytest.raises(DBAPIError, match="permission denied"):
            await db.execute(text(statement))


async def test_the_role_writes_the_agent_schema(database: Database) -> None:
    async with database.db_session_factory() as db:
        person = await db.scalar(text("SELECT person_id FROM sag.person LIMIT 1"))
        await db.execute(
            text(
                "INSERT INTO agent.conversation (id, person_id) VALUES (gen_random_uuid(), :person)"
            ),
            {"person": person},
        )
        assert await db.scalar(text("SELECT nextval('agent.protocol_number_seq')")) is not None
        await db.rollback()
