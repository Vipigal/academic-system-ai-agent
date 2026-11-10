import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from api.application.finance.service import FinancialService
from api.domain.identity.session import StudentSession
from api.persistence.core.database import Database
from api.persistence.identity.student_session_repository import StudentSessionRepository
from tests.doubles.database import application_database, database_at
from tests.integration.support.owned import Owned, owned_by
from tests.integration.support.sql_oracle import SqlOracle, admin_url
from tests.integration.support.tools import tools_factory

ONE_ID_PER_PERSON = (
    r"SELECT min(person_id) FROM sag.person GROUP BY regexp_replace(cpf, '\D', '', 'g')"
)


@pytest.fixture
async def database() -> AsyncIterator[Database]:
    connected = application_database()
    yield connected
    await connected.dispose()


@pytest.fixture
async def admin_database() -> AsyncIterator[Database]:
    connected = database_at(admin_url())
    yield connected
    await connected.dispose()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def everyone() -> AsyncIterator[list[StudentSession]]:
    connected = application_database()
    people = await SqlOracle().values(ONE_ID_PER_PERSON)
    repository = StudentSessionRepository(connected)
    yield list(await asyncio.gather(*(repository.load(person_id) for person_id in sorted(people))))
    await connected.dispose()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def owned_by_everyone(everyone: list[StudentSession]) -> AsyncIterator[list[Owned]]:
    connected = application_database()
    yield list(await asyncio.gather(*(owned_by(connected, session) for session in everyone)))
    await connected.dispose()


@pytest.fixture
async def financial_services(
    database: Database, everyone: list[StudentSession]
) -> list[FinancialService]:
    factory = tools_factory(database)
    return [await factory.of_session(session, FinancialService) for session in everyone]
