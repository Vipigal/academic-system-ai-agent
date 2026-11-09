import pytest
import pytest_asyncio

from api.bootstrap.settings import Settings
from api.persistence.core.database import Database
from api.persistence.identity.student_session_repository import StudentSessionRepository
from tests.integration.agent import invariant_queries, invariant_volumes
from tests.integration.support.owned import owned_by
from tests.integration.support.sql_oracle import SqlOracle
from tests.integration.support.tools import tools_factory


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def people() -> list[str]:
    connected = Database(Settings.from_environment().database_url.get_secret_value())
    found = await SqlOracle().values(invariant_queries.SAMPLE_PEOPLE, scope="full")
    await connected.dispose()
    return sorted(found)


@pytest.fixture
async def volumes(database: Database, people: list[str]) -> list[invariant_volumes.Volumes]:
    factory = tools_factory(database)
    repository = StudentSessionRepository(database)
    return [
        invariant_volumes.Volumes(
            SqlOracle(),
            await factory.for_person(person),
            await owned_by(database, await repository.load(person)),
        )
        for person in people
    ]


async def test_online_exam_attempts_match_the_attempts_of_the_own_accounts(
    volumes: list[invariant_volumes.Volumes],
) -> None:
    counts = [await person.attempts() for person in volumes]
    assert sum(count.expected for count in counts) > 0
    assert all(count.returned == count.expected for count in counts)


@pytest.mark.sweep
@pytest.mark.slow
async def test_material_views_match_the_view_events_of_the_own_accounts(
    volumes: list[invariant_volumes.Volumes],
) -> None:
    counts = [count for person in volumes for count in await person.views()]
    assert sum(count.expected for count in counts) > 0
    assert all(count.returned == count.expected for count in counts)


async def test_protocol_messages_and_history_match_the_public_rows(
    volumes: list[invariant_volumes.Volumes],
) -> None:
    counts = [count for person in volumes for count in await person.protocols()]
    assert sum(count.expected for count in counts) > 0
    assert all(count.returned == count.expected for count in counts)
