import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from api.application.financial_service import FinancialService
from api.domain.session import StudentSession
from api.persistence.database import Database
from api.persistence.student_session_repository import StudentSessionRepository
from api.settings import Settings
from tests.integration.sql_oracle import SqlOracle
from tests.integration.tool_support import tools_factory

ONE_ID_PER_PERSON = (
    r"SELECT min(person_id) FROM sag.person GROUP BY regexp_replace(cpf, '\D', '', 'g')"
)


@pytest.fixture
async def database() -> AsyncIterator[Database]:
    connected = Database(Settings.from_environment().database_url.get_secret_value())
    yield connected
    await connected.dispose()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def everyone() -> AsyncIterator[list[StudentSession]]:
    connected = Database(Settings.from_environment().database_url.get_secret_value())
    people = await SqlOracle(connected).values(ONE_ID_PER_PERSON)
    repository = StudentSessionRepository(connected.db_session_factory)
    yield list(await asyncio.gather(*(repository.load(person_id) for person_id in sorted(people))))
    await connected.dispose()


@pytest.fixture
def financial_services(
    database: Database, everyone: list[StudentSession]
) -> list[FinancialService]:
    factory = tools_factory(database)
    return [factory.services_for(session).financial() for session in everyone]
